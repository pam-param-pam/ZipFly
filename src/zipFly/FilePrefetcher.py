import asyncio
import contextlib
from typing import List, Optional, AsyncGenerator

from .LazyList import LazyList


class _SingleFilePrefetch:
    """Handles a single file's async queue and task."""

    def __init__(self, file, queue_maxsize: int = 2):
        self.file = file
        self.queue = asyncio.Queue(maxsize=queue_maxsize)
        self.task: Optional[asyncio.Task] = None
        self.error: Optional[BaseException] = None
        self._agen = None

    async def start(self):
        self.task = asyncio.create_task(self._prefetch())

    async def _prefetch(self):
        self._agen = self.file.async_generate_processed_file_data()

        try:
            async for chunk in self._agen:
                await self.queue.put(chunk)

        except asyncio.CancelledError:
            await self._close_generator()
            raise

        except GeneratorExit:
            await self._close_generator()
            raise

        except BaseException as exc:
            self.error = exc
            await self._put_sentinel()

        else:
            await self._put_sentinel()

        finally:
            self._agen = None

    async def _put_sentinel(self):
        # Do not suppress CancelledError here.
        # If the prefetcher is being cancelled, cancellation should propagate.
        await self.queue.put(None)

    async def _close_generator(self):
        agen = self._agen
        self._agen = None

        if agen is not None:
            with contextlib.suppress(Exception):
                await agen.aclose()

    async def wait(self):
        if self.task is not None:
            await self.task
            self.task = None

        if self.error is not None:
            raise self.error

    async def cancel(self):
        if self.task is None:
            return

        task = self.task
        self.task = None

        if not task.done():
            task.cancel()

        with contextlib.suppress(asyncio.CancelledError):
            await task

        if task.done() and not task.cancelled():
            with contextlib.suppress(Exception):
                task.exception()

        await self._close_generator()

class FilePrefetcher:
    def __init__(self, files: LazyList, prefetch_files: int = 20, queue_maxsize: int = 2):
        self.files = files
        self.prefetch_files = prefetch_files
        self.queue_maxsize = queue_maxsize

        # Do NOT call len(files). That consumes LazyList.
        self.prefetchers: List[Optional[_SingleFilePrefetch]] = []

        self.inflight = 0
        self.next_to_start = 0
        self.exhausted = False
        self.closed = False

    def get_file(self, idx: int):
        pf = self.prefetchers[idx]

        if pf is None:
            raise RuntimeError(f"Prefetcher for file {idx} was not started")

        return pf.file

    def _ensure_slot(self, idx: int) -> None:
        while len(self.prefetchers) <= idx:
            self.prefetchers.append(None)

    async def _start_prefetch(self, idx: int) -> bool:
        if self.closed:
            return False

        self._ensure_slot(idx)

        # Already prefetched. This is valid even after source exhaustion.
        if self.prefetchers[idx] is not None:
            return True

        if self.exhausted:
            return False

        try:
            file = self.files[idx]
        except IndexError:
            self.exhausted = True
            return False

        pf = _SingleFilePrefetch(file, self.queue_maxsize)
        self.prefetchers[idx] = pf

        await pf.start()

        self.inflight += 1
        self.next_to_start = max(self.next_to_start, idx + 1)

        return True

    async def _refill_window(self) -> None:
        while not self.closed and not self.exhausted and self.inflight < self.prefetch_files:
            started = await self._start_prefetch(self.next_to_start)
            if not started:
                break

    async def ensure_prefetch(self, idx: int):
        """Ensure the prefetcher for file `idx` is started, then refill the window."""

        if self.closed:
            raise RuntimeError("FilePrefetcher is closed")

        # Already started/prefetched: OK even if self.exhausted is True.
        if idx < len(self.prefetchers) and self.prefetchers[idx] is not None:
            await self._refill_window()
            return

        # Not already started, and source is exhausted: this index does not exist.
        if self.exhausted:
            raise IndexError(idx)

        started = await self._start_prefetch(idx)

        if not started:
            raise IndexError(idx)

        await self._refill_window()

    async def stream_file_data(self, idx: int) -> AsyncGenerator[bytes, None]:
        """Yield chunks of one file in order."""
        await self.ensure_prefetch(idx)

        pf = self.prefetchers[idx]
        if pf is None:
            raise RuntimeError(f"Prefetcher for file {idx} was not started")

        while True:
            chunk = await pf.queue.get()

            if chunk is None:
                await pf.wait()
                self.inflight -= 1
                await self._refill_window()
                break

            yield chunk

    async def aclose(self) -> None:
        """Cancel all background prefetch tasks."""
        if self.closed:
            return

        self.closed = True

        tasks = [
            pf.cancel()
            for pf in self.prefetchers
            if pf is not None
        ]

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        self.inflight = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.aclose()
