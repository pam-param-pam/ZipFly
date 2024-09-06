import datetime
import time
from typing import Generator

from zipstream import consts
from zipstream.BaseFile import BaseFile


class GenFile(BaseFile):

    def __init__(self, file_path: str, generator: Generator, size: int, modification_time):
        super().__init__()
        self._file_path = file_path
        self.generator = generator
        self._size = size
        self._modification_time = modification_time

    def generate_file_data(self) -> Generator:
        yield from self.generator

    @property
    def file_path(self):
        return self._file_path

    @property
    def size(self) -> int:
        return self._size

    @property
    def modification_time(self):
        return self._modification_time

    @property
    def is_size_known(self):
        return True

    @property
    def compression_method(self) -> int:
        return 0  # no compression


