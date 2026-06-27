import time
import zlib
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Generator
from typing import Optional

from . import consts
from .Compressor import Compressor
from .consts import DATA_DESCRIPTOR_FLAG


class BaseFile(ABC):
    """DO NOT REUSE BaseFile instances!"""
    def __init__(self, name: str, compression_method: int = consts.NO_COMPRESSION, custom_payload: bytes = b""):
        self.__used = False
        self.__compressed_size = 0
        self.__size = 0
        self.__offset = 0  # Offset to local file header
        self.__crc = 0
        self.__compression_method = compression_method
        self.__flags = DATA_DESCRIPTOR_FLAG
        self.__finished_file_data_streaming = False

        if len(custom_payload) > 0xFFFF:
            raise ValueError("ZIP extra field payload too large")
        self.__custom_payload = custom_payload

        if name == "":
            raise ValueError("File name cannot be blank.")
        self._name = name

    def __str__(self):
        return f"BaseFile[name={self._name}]"

    def __repr__(self):
        return f"BaseFile({self._name})"

    def _check_if_used(self):
        if self.__used:
            raise RuntimeError("Do not re-use file instances. Recreate it.")
        self.__used = True

    def generate_processed_file_data(self) -> Generator[bytes, None, None]:
        """Generates compressed file data"""
        self._check_if_used()
        compressor = Compressor(self)

        for chunk in self._generate_file_data():
            chunk = compressor.process(chunk)
            if len(chunk) > 0:
                yield chunk
        chunk = compressor.tail()
        if len(chunk) > 0:
            yield chunk

        self._finish_and_validate()

    async def async_generate_processed_file_data(self) -> AsyncGenerator[bytes, None]:
        """Generates compressed file data"""
        self._check_if_used()
        compressor = Compressor(self)

        async for chunk in self._async_generate_file_data():
            chunk = compressor.process(chunk)
            if len(chunk) > 0:
                yield chunk
        chunk = compressor.tail()
        if len(chunk) > 0:
            yield chunk

        self._finish_and_validate()

    def can_make_local_extra_field(self) -> bool:
        # Here we check if we can include offsets before file data(if its known before streaming)
        return (
            self.predicted_crc is not None
            and self.predicted_size is not None
            and self.compression_method == consts.NO_COMPRESSION
        )

    def mark_finished_file_data_streaming(self):
        self.__finished_file_data_streaming = True

    def _finish_and_validate(self):
        self.__finished_file_data_streaming = True
        if self.predicted_size is not None and self.predicted_size != self.size:
            raise RuntimeError(f"Size({self.predicted_size}) != streamed size({self.size})")

        if self.predicted_crc is not None and self.predicted_crc != self.crc:
            raise RuntimeError(f"Crc({self.predicted_crc}) != streamed crc({self.crc})")

    def get_mod_time(self) -> int:
        # Extract hours, minutes, and seconds from the modification time
        t = time.localtime(self.modification_time)
        return ((t.tm_hour << 11) | (t.tm_min << 5) | (t.tm_sec // 2)) & 0xFFFF

    def get_mod_date(self) -> int:
        # Extract year, month, and day from the modification time
        t = time.localtime(self.modification_time)
        year = t.tm_year - 1980  # ZIP format years start from 1980
        return ((year << 9) | (t.tm_mon << 5) | t.tm_mday) & 0xFFFF

    def set_offset(self, new_offset) -> None:
        self.__offset = new_offset

    def add_size(self, value) -> None:
        self.__size += value

    def add_compressed_size(self, value) -> None:
        self.__compressed_size += value

    def set_compressed_size(self, new_value) -> None:
        self.__compressed_size = new_value

    def set_size(self, new_value) -> None:
        self.__size = new_value

    def set_crc(self, new_crc) -> None:
        self.__crc = new_crc

    def set_file_name(self, new_name: str) -> None:
        self._name = new_name

    def update_current_crc(self, chunk):
        self.__crc = zlib.crc32(chunk, self.__crc)

    @property
    def custom_payload(self) -> bytes:
        return self.__custom_payload

    @property
    def offset(self) -> int:
        return self.__offset

    @property
    def file_path_bytes(self) -> bytes:
        try:
            return self.name.encode("ascii")
        except UnicodeError:
            self.__flags |= consts.UTF8_FLAG
            return self.name.encode()

    @property
    def flags(self) -> int:
        _ = self.file_path_bytes  # trigger to set utf8 flag if needed
        return self.__flags

    @property
    def name(self) -> str:
        return self._name

    @property
    def compression_method(self) -> int:
        return self.__compression_method

    @property
    def compressed_size(self) -> int:
        if not self.__finished_file_data_streaming:
            raise RuntimeError("Compressed size called before file data finished streaming. Use predicted_compressed_size instead.")
        return self.__compressed_size

    @property
    def size(self) -> int:
        if not self.__finished_file_data_streaming:
            raise RuntimeError("Size called before file data finished streaming. Use predicted_size instead.")
        return self.__size

    @property
    def crc(self) -> int:
        if not self.__finished_file_data_streaming:
            raise RuntimeError("Crc called before file data finished streaming. Use predicted_crc instead.")
        return self.__crc

    @property
    @abstractmethod
    def modification_time(self) -> float:
        raise NotImplementedError

    @property
    @abstractmethod
    def predicted_crc(self) -> Optional[int]:
        raise NotImplementedError

    @property
    @abstractmethod
    def predicted_size(self) -> Optional[int]:
        raise NotImplementedError

    @abstractmethod
    def _generate_file_data(self) -> Generator[bytes, None, None]:
        raise NotImplementedError

    @abstractmethod
    async def _async_generate_file_data(self) -> AsyncGenerator[bytes, None]:
        raise NotImplementedError
