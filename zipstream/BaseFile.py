from abc import ABC, abstractmethod
from typing import Generator


class BaseFile(ABC):
    def __init__(self):
        self.org_size = 0,  # Original uncompressed size
        self.compr_size = 0,  # Compressed size
        self.offset = 0,  # Offset of local file header
        self.crc = 0

    @abstractmethod
    def generate_file_data(self) -> Generator:
        raise NotImplementedError

    def __str__(self):
        return f"FILE[{self.name_path}]"

    @property
    def name_path(self) -> str:
        raise NotImplementedError

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
    def compression_method(self):
        raise NotImplementedError
