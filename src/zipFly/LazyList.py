from collections.abc import Iterable, Iterator
from itertools import islice
from typing import Generic, TypeVar, overload, Union

T = TypeVar("T")


class LazyList(Generic[T]):
    def __init__(self, iterable: Iterable[T]):
        self._iterator: Iterator[T] = iter(iterable)
        self._cache: list[T] = []
        self._exhausted = False

    def __iter__(self) -> Iterator[T]:
        for item in self._cache:
            yield item

        while not self._exhausted:
            try:
                item = next(self._iterator)
            except StopIteration:
                self._exhausted = True
                break

            self._cache.append(item)
            yield item

    def _fill_to(self, index: int) -> None:
        if index < 0:
            self._consume_all()
            return

        while len(self._cache) <= index and not self._exhausted:
            try:
                self._cache.append(next(self._iterator))
            except StopIteration:
                self._exhausted = True
                break

    def _consume_all(self) -> None:
        while not self._exhausted:
            try:
                self._cache.append(next(self._iterator))
            except StopIteration:
                self._exhausted = True
                break

    def _iter_slice(self, index: slice) -> Iterator[T]:
        start = index.start
        stop = index.stop
        step = index.step

        if step == 0:
            raise ValueError("slice step cannot be zero")

        if (
            (start is not None and start < 0)
            or (stop is not None and stop < 0)
            or (step is not None and step < 0)
        ):
            self._consume_all()
            yield from self._cache[index]
            return

        yield from islice(iter(self), start, stop, step)

    def lazy_slice(self, index: slice) -> "LazyList[T]":
        return LazyList(self._iter_slice(index))

    def from_index(self, start: int) -> "LazyList[T]":
        return self.lazy_slice(slice(start, None))

    def __len__(self):
        self._consume_all()
        return len(self._cache)

    @overload
    def __getitem__(self, index: int) -> T:
        ...

    @overload
    def __getitem__(self, index: slice) -> "LazyList[T]":
        ...

    def __getitem__(self, index: Union[int,  slice]) -> Union[T, Iterator[T]]:
        if isinstance(index, slice):
            return self.lazy_slice(index)

        self._fill_to(index)

        try:
            return self._cache[index]
        except IndexError:
            raise IndexError(index)
