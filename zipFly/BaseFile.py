from abc import ABC, abstractmethod
from typing import Generator

from zipFly import consts
from zipFly.Compressor import Compressor


class BaseFile(ABC):
    def __init__(self, compression_method):
        self.original_size = 0
        self.compressed_size = 0
        self.offset = 0  # Offset of local file header
        self.crc = 0
        self.flags = 0b00001000  # flag about using data descriptor is always on
        self.compression_method = compression_method or consts.NO_COMPRESSION
        self.test = "test"

    def generate_processed_file_data(self) -> Generator:
        compressor = Compressor(self)

        """
        Generates compressed file data
        """
        for chunk in self._generate_file_data():
            chunk = compressor.process(chunk)
            if len(chunk) > 0:
                yield chunk
            chunk = compressor.tail()
            if len(chunk) > 0:
                yield chunk

    @abstractmethod
    def _generate_file_data(self) -> Generator:
        raise NotImplementedError

    def __str__(self):
        return f"FILE[{self.name}]"

    @property
    def size(self) -> int:
        raise NotImplementedError

    @property
    def modification_time(self):
        raise NotImplementedError

    def get_mod_time(self):
        return int(self.modification_time) & 0xFFFF

    def get_mod_date(self):
        return int(self.modification_time / 86400 + 365 * 20) & 0xFFFF

    @property
    def name(self):
        raise NotImplementedError

    @property
    def file_path_bytes(self) -> bytes:
        try:
            return self.name.encode("ascii")
        except UnicodeError:
            self.flags |= consts.UTF8_FLAG
            return self.name.encode("utf-8")
