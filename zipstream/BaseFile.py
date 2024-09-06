from abc import ABC, abstractmethod
from typing import Generator

from zipstream import consts


class BaseFile(ABC):
    def __init__(self):
        self.original_size = 0
        self.compressed_size = 0
        self.offset = 0  # Offset of local file header
        self.crc = 0
        self.flags = 0b00001000  # flag about using data descriptor is always on

    @abstractmethod
    def generate_file_data(self) -> Generator:
        raise NotImplementedError

    def __str__(self):
        return f"FILE[{self.file_path}]"

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
    def is_size_known(self):
        raise NotImplementedError

    @property
    def file_path(self):
        raise NotImplementedError

    @property
    def compression_method(self) -> int:
        raise NotImplementedError

    @property
    def file_path_bytes(self) -> bytes:
        try:
            return self.file_path.encode("ascii")
        except UnicodeError:
            self.flags |= consts.UTF8_FLAG
            return self.file_path.encode("utf-8")
