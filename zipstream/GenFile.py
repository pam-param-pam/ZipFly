import datetime
import time
from typing import Generator

from zipstream import consts
from zipstream.BaseFile import BaseFile


class GenFile(BaseFile):

    def __init__(self, name_path: str, generator: Generator, size: int): #, modification_time: localtime
        super().__init__()
        self._name_path = name_path
        self.generator = generator
        self._size = size
        self._modification_time = time.time()

    def generate_file_data(self) -> Generator:
        yield from self.generator

    @property
    def name_path(self) -> bytes:
        try:
            return self._name_path.encode("ascii")
        except UnicodeError:
            return self._name_path.encode("utf-8")
            #self.flags |= consts.UTF8_FLAG

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
    def compression_method(self):
        return None



