import os
from typing import Generator

from zipstream.BaseFile import BaseFile


class LocalFile(BaseFile):
    def __init__(self, file_path):
        super().__init__()
        self._file_path = file_path
        self.chunk_size = 1048

    def generate_file_data(self) -> Generator:
        with open(self.file_path, 'rb') as file:
            while True:
                chunk = file.read(self.chunk_size)
                if not chunk:
                    break
                yield chunk

    @property
    def name_path(self) -> str:
        return self.file_path

    @property
    def file_path(self):
        return self._file_path
    @property
    def size(self) -> int:
        return os.path.getsize(self.file_path)


    @property
    def modification_time(self):
        return os.path.getmtime(self.file_path)

    @property
    def is_size_known(self):
        return True

    @property
    def compression_method(self) -> int:
        return 0  # no compression