import time
from typing import Generator, AsyncGenerator, Union, Optional

from . import consts
from .BaseFile import BaseFile


class GenFile(BaseFile):
    def __init__(self, name: str, generator: Union[Generator[bytes, None, None], AsyncGenerator[bytes, None]], compression_method: int = consts.NO_COMPRESSION,
                 modification_time: float = None, size: int = None, crc: int = None, custom_payload: bytes = b""):
        if size and compression_method != consts.NO_COMPRESSION:
            raise ValueError("File size is allowed only with NO_COMPRESSION")

        if crc and compression_method != consts.NO_COMPRESSION:
            raise ValueError("File crc is allowed only with NO_COMPRESSION")

        self._generator = generator
        self._predicted_size = size
        self._predicted_crc = crc
        self._modification_time = modification_time if modification_time else time.time()

        self._streamed_size = 0
        super().__init__(name=name, compression_method=compression_method, custom_payload=custom_payload)

    def __str__(self):
        return f"GenFile[name={self.name}]"

    def __repr__(self):
        return f"GenFile({self.name})"

    def _get_generator(self):
        return self._generator

    def _generate_file_data(self) -> Generator[bytes, None, None]:
        generator = self._get_generator()
        if isinstance(generator, Generator):
            for chunk in generator:
                self._streamed_size += len(chunk)
                yield chunk
        else:
            raise ValueError(f"generator must be of type Generator, not '{type(generator)}'")

    async def _async_generate_file_data(self) -> AsyncGenerator[bytes, None]:
        generator = self._get_generator()
        if isinstance(generator, AsyncGenerator):
            async for chunk in generator:
                self._streamed_size += len(chunk)
                yield chunk
        else:
            raise ValueError(f"generator must be of type AsyncGenerator, not '{type(generator)}'")

    @property
    def modification_time(self) -> float:
        return self._modification_time

    @property
    def predicted_crc(self) -> Optional[int]:
        return self._predicted_crc

    @property
    def predicted_size(self) -> Optional[int]:
        return self._predicted_size
