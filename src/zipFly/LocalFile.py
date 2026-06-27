import os
import zlib
from pathlib import Path
from typing import Generator, AsyncGenerator, Union, Optional

import aiofiles

from . import consts
from .BaseFile import BaseFile


class LocalFile(BaseFile):
    def __init__(self, file_path: Union[str, Path], name: str = None, compression_method: int = consts.NO_COMPRESSION, chunk_size=None, custom_payload: bytes = b""):
        file_path = Path(file_path)
        if not file_path.is_file():
            raise ValueError(f"{file_path} is not a correct file path.")

        self._file_path = str(file_path)
        self.chunk_size = chunk_size
        self.__crc = None

        name = name if name else self._file_path
        super().__init__(name=name, compression_method=compression_method, custom_payload=custom_payload)

    def __str__(self):
        return f"LocalFile[name={self.name}]"

    def __repr__(self):
        return f"LocalFile({self.name})"

    async def _async_generate_file_data(self) -> AsyncGenerator[bytes, None]:
        if not self.chunk_size:
            self.chunk_size = 1048 * 1048 * 4

        async with aiofiles.open(self._file_path, "rb") as fh:
            while True:
                part = await fh.read(self.chunk_size)
                if not part:
                    break
                yield part

    def _generate_file_data(self) -> Generator[bytes, None, None]:
        if not self.chunk_size:
            self.chunk_size = 1048 * 16

        with open(self._file_path, 'rb') as file:
            while True:
                chunk = file.read(self.chunk_size)
                if not chunk:
                    break
                yield chunk

    @property
    def modification_time(self) -> float:
        """Returns the modification time as a Unix timestamp"""
        return os.path.getmtime(self._file_path)

    @property
    def predicted_size(self) -> Optional[int]:
        return os.path.getsize(self._file_path)

    @property
    def predicted_crc(self) -> Optional[int]:
        if self.__crc is None:
            crc = 0

            with open(self._file_path, "rb") as f:
                while chunk := f.read(self.chunk_size):
                    crc = zlib.crc32(chunk, crc)

            self.__crc = crc & 0xFFFFFFFF

        return self.__crc
