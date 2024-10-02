import os
import time
from typing import Generator, AsyncGenerator
from zipFly.BaseFile import BaseFile

import aiofiles

class LocalFile(BaseFile):

    async def _async_generate_file_data(self) -> AsyncGenerator[bytes, None]:

        async with aiofiles.open(self._file_path, "rb") as fh:
            while True:
                part = await fh.read(self.chunk_size)
                if not part:
                    break
                yield part

    def __init__(self, file_path: str, name: str = None, compression_method: int = None):
        if not os.path.isfile(file_path):
            raise ValueError(f"{file_path} is not a correct file path.")
        self._file_path = file_path
        self.chunk_size = 1048
        self._name = name if name else file_path
        super().__init__(compression_method)

    def _generate_file_data(self) -> Generator[bytes, None, None]:
        with open(self._file_path, 'rb') as file:
            while True:
                chunk = file.read(self.chunk_size)
                if not chunk:
                    break
                yield chunk

    @property
    def name(self) -> str:
        return self._name

    @property
    def size(self) -> int:
        return os.path.getsize(self._file_path)

    @property
    def modification_time(self) -> float:
        return os.path.getmtime(self._file_path)

    def get_mod_time(self) -> int:
        # Extract hours, minutes, and seconds from the modification time
        t = time.localtime(self.modification_time)
        return ((t.tm_hour << 11) | (t.tm_min << 5) | (t.tm_sec // 2)) & 0xFFFF

    def get_mod_date(self) -> int:
        # Extract year, month, and day from the modification time
        t = time.localtime(self.modification_time)
        year = t.tm_year - 1980  # ZIP format years start from 1980
        return ((year << 9) | (t.tm_mon << 5) | t.tm_mday) & 0xFFFF

    def set_file_name(self, new_name: str) -> None:
        self._name = new_name
