import time
from typing import Generator, AsyncGenerator

from .BaseFile import BaseFile


class EmptyFolder(BaseFile):
    def __init__(self, name: str, modification_time: float = None):
        super().__init__(name)
        if not name.endswith("/"):
            name += "/"
        self._name = name
        self._modification_time = modification_time if modification_time else time.time()
        self._finished_streaming = False

    def __str__(self):
        return f"EmptyFolder[name={self.name}]"

    def __repr__(self):
        return f"EmptyFolder({self.name})"

    def _generate_file_data(self) -> Generator[bytes, None, None]:
        yield b''

    async def _async_generate_file_data(self) -> AsyncGenerator[bytes, None]:
        yield b''

    @property
    def predicted_crc(self) -> int:
        return 0

    @property
    def predicted_size(self) -> int:
        return 0

    @property
    def modification_time(self) -> float:
        return self._modification_time
