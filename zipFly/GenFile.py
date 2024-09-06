from typing import Generator
from zipFly.BaseFile import BaseFile


class GenFile(BaseFile):

    def __init__(self, name: str, generator: Generator, compression_method=None, modification_time=None, size: int = None):
        super().__init__(compression_method)
        self._name = name
        self.generator = generator
        self._size = size
        self._modification_time = modification_time

    def _generate_file_data(self) -> Generator:
        yield from self.generator

    @property
    def name(self) -> str:
        return self._name

    @property
    def size(self) -> int:
        if self._size:
            return self._size
        raise ValueError("size not known before streaming")

    @property
    def modification_time(self):
        return self._modification_time


