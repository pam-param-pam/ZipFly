from typing import Generator, AsyncGenerator, Union, AsyncIterable, Iterable, Iterator, Sequence

from . import consts
from .BaseFile import BaseFile
from .FilePrefetcher import FilePrefetcher
from .LazyList import LazyList
from .ZipBase import ZipBase


def process_file_names(files: Iterable[BaseFile]) -> Iterator[BaseFile]:
    """Renames duplicated file names lazily."""
    seen_names: set[str] = set()

    for file in files:
        base, ext = file.name.rsplit(".", 1) if "." in file.name else (file.name, "")
        ext = f".{ext}" if ext else ""

        counter = 0
        new_name = f"{base}{ext}"

        while new_name in seen_names:
            counter += 1
            new_name = f"{base} ({counter}){ext}"

        file.set_file_name(new_name)
        seen_names.add(new_name)

        yield file

def is_lazy_files_iterable(files: Iterable[BaseFile]) -> bool:
    if isinstance(files, list):
        return False

    if isinstance(files, Sequence):
        return False

    return True

class ZipFly(ZipBase):
    def __init__(self, files: Iterable[BaseFile], byte_offset: int = 0):
        super().__init__()
        self._files = LazyList(process_file_names(files))

        self._LOCAL_FILE_HEADER_SIZE = 30
        self._ZIP64_LOCAL_EXTRA_FIELD_SIZE = 20
        self._DATA_DESCRIPTOR_SIZE = 24
        self._CENTRAL_DIR_HEADER_SIZE = 46
        self._ZIP64_CDIR_EXTRA_FIELD_SIZE = 28
        self._ZIP64_END_OF_CDIR_RECORD_SIZE = 56
        self._ZIP64_END_OF_CDIR_LOCATOR_SIZE = 20
        self._END_OF_CDIR_RECORD_CD_RECORD_SIZE = 22

        self._remaining_offset = 0
        self.__used = False
        self._byte_offset = byte_offset
        self._lazy_files = is_lazy_files_iterable(files)

    def was_used(self) -> bool:
        return self.__used

    def calculate_archive_size(self) -> int:
        """Calculates total archive size. Raises an error if it can't"""
        if self._lazy_files:
            raise RuntimeError("Cannot calculate archive size for lazy files. Use a list of files instead.")

        total_size = 0

        for file in self._files:
            total_size += self._calculate_file_size_in_archive(file)
            central_directory_header_size = self._CENTRAL_DIR_HEADER_SIZE + len(file.file_path_bytes) + self._ZIP64_CDIR_EXTRA_FIELD_SIZE
            total_size += central_directory_header_size

        total_size += self._ZIP64_END_OF_CDIR_RECORD_SIZE
        total_size += self._ZIP64_END_OF_CDIR_LOCATOR_SIZE
        total_size += self._END_OF_CDIR_RECORD_CD_RECORD_SIZE

        return total_size

    def _calculate_file_size_in_archive(self, file: BaseFile):
        """Returns the size of: [local file header] + [LOCAL EXTRA FIELD] + [file data] + [data descriptor]"""
        block_size = 0

        local_file_header_size = self._LOCAL_FILE_HEADER_SIZE + len(file.file_path_bytes)
        block_size += local_file_header_size

        if file.can_make_local_extra_field():
            block_size += self._ZIP64_LOCAL_EXTRA_FIELD_SIZE

        if file.custom_payload:
            block_size += 4 + len(file.custom_payload)

        block_size += file.predicted_size
        block_size += self._DATA_DESCRIPTOR_SIZE

        return block_size

    def _find_starting_file(self) -> Union[tuple[int, int], tuple[None, int]]:
        """This function is used in byte_offset mode. It finds the file in which byte offset is located.
        Returns:
            A tuple containing the index of the file and the offset within the file if found, otherwise tuple[None, remaining_offset].
        Raises:
            ValueError
        """
        if not self._byte_offset:  # skip if not using byte_offset mode
            return 0, 0

        if not self._lazy_files:
            if self._byte_offset > self.calculate_archive_size():
                raise ValueError("Byte offset > total archive size")

        running_offset = 0
        for index, file in enumerate(self._files):

            file_size_in_archive = self._calculate_file_size_in_archive(file)

            # We must set offset for files bcs the offset won't be handled by the usual parts of the code bcs we are skipping them later on
            file.set_offset(running_offset)

            if running_offset <= self._byte_offset < running_offset + file_size_in_archive:
                return index, self._byte_offset - running_offset

            if file.compression_method != consts.NO_COMPRESSION:
                raise ValueError("Byte offset is supported only for non compressed files")

            # We must set both crc and compressed size for the files in the archive that we entirely "skip"
            file.set_crc(file.predicted_crc)
            file.set_compressed_size(file.predicted_size)
            file.set_size(file.predicted_size)
            file.mark_finished_file_data_streaming()

            running_offset += file_size_in_archive

        return None, self._byte_offset - running_offset

    def _make_end_structures(self) -> Generator[bytes, None, None]:
        """
        Make zip64 end structures, which include:
            central directory file header for every file
            zip64 extra field for every file
            zip64 end of central dir record
            zip64 end of central dir locator
            end of central dir record
        """
        # Save offset to start of central dir for zip64 end of cdir record
        self._offset_to_start_of_central_dir = self._get_offset()

        # Stream central directory entries
        for file in self._files:
            chunk = self._make_cdir_file_header(file)
            chunk += self._make_cdir_zip64_extra_field(file)
            self._add_cdir_size(len(chunk))
            chunk = self._apply_remaining_offset(chunk)
            self._add_offset(len(chunk))

            yield chunk

        yield self._apply_remaining_offset(self._make_zip64_end_of_cdir_record(total_files=len(self._files)))

        yield self._apply_remaining_offset(self._make_zip64_end_of_cdir_locator())

        yield self._apply_remaining_offset(self._make_end_of_cdir_record(total_files=len(self._files)))

    def _stream_single_file_prefix(self, file: BaseFile) -> Generator[bytes, None, None]:
        """
        Stream local file header and optional local ZIP64 extra field.
        """
        yield self._apply_remaining_offset(self._make_local_file_header(file))

        if file.can_make_local_extra_field():
            yield self._apply_remaining_offset(self._make_local_zip64_extra_field(file))

        if file.custom_payload:
            yield self._apply_remaining_offset(self._make_custom_extra_field(file))

    async def _async_stream_single_file_from_data(self, file: BaseFile, data_chunks: AsyncIterable[bytes]) -> AsyncGenerator[bytes, None]:
        """
        Stream a single file using an externally supplied async data source.

        Used by:
        - _async_stream_single_file
        - async_stream_parallel
        """
        for chunk in self._stream_single_file_prefix(file):
            yield chunk

        async for chunk in data_chunks:
            yield self._apply_remaining_offset(chunk)

        yield self._apply_remaining_offset(self._make_data_descriptor(file))

    async def _async_stream_single_file(self, file: BaseFile) -> AsyncGenerator[bytes, None]:
        """This function streams a single file, it also applies remaining_offset if needed"""
        async for chunk in self._async_stream_single_file_from_data(file, file.async_generate_processed_file_data()):
            yield chunk

    def _stream_single_file(self, file: BaseFile) -> Generator[bytes, None, None]:
        """
        stream single zip file with header and descriptor at the end.
        """
        for chunk in self._stream_single_file_prefix(file):
            yield chunk

        for chunk in file.generate_processed_file_data():
            yield self._apply_remaining_offset(chunk)

        yield self._apply_remaining_offset(self._make_data_descriptor(file))

    async def async_stream(self) -> AsyncGenerator[bytes, None]:
        """Streams the entire archive asynchronously"""
        self._check_if_can_stream()
        starting_file_index, remaining_offset = self._find_starting_file()
        self._remaining_offset = remaining_offset

        self._set_offset(self._byte_offset - remaining_offset)
        if starting_file_index is not None:
            for file in self._files[starting_file_index:]:
                file.set_offset(self._get_offset())
                async for chunk in self._async_stream_single_file(file):
                    self._add_offset(len(chunk))
                    yield chunk

        # stream zip structures
        for chunk in self._make_end_structures():
            yield chunk

    async def async_stream_parallel(self, prefetch_files: int = 20, max_chunks_per_file: int = 2):
        """
        Stream files in parallel.
        - prefetch_files: number of files' DATA to read ahead concurrently
        - max_chunks_per_file: per-file buffered DATA chunks (backpressure)
        """
        self._check_if_can_stream()

        start_idx, remaining_offset = self._find_starting_file()
        self._remaining_offset = remaining_offset
        self._set_offset(self._byte_offset - remaining_offset)

        prefetch_mgr = None

        try:
            if start_idx is not None:
                files = self._files[start_idx:]
                prefetch_mgr = FilePrefetcher(files, prefetch_files, max_chunks_per_file)

                i = 0

                while True:
                    try:
                        await prefetch_mgr.ensure_prefetch(i)
                    except IndexError:
                        break

                    file = prefetch_mgr.get_file(i)

                    file.set_offset(self._get_offset())

                    async for chunk in self._async_stream_single_file_from_data(file, prefetch_mgr.stream_file_data(i)):
                        self._add_offset(len(chunk))

                        if chunk:
                            yield chunk

                    i += 1

            for chunk in self._make_end_structures():
                yield chunk

        finally:
            if prefetch_mgr is not None:
                await prefetch_mgr.aclose()

    def stream(self) -> Generator[bytes, None, None]:
        self._check_if_can_stream()

        starting_file_index, remaining_offset = self._find_starting_file()
        self._remaining_offset = remaining_offset

        self._set_offset(self._byte_offset - remaining_offset)
        if starting_file_index is not None:
            for file in self._files[starting_file_index:]:
                file.set_offset(self._get_offset())
                for chunk in self._stream_single_file(file):
                    self._add_offset(len(chunk))
                    yield chunk

        # stream zip structures
        for chunk in self._make_end_structures():
            yield chunk

    def _check_if_can_stream(self):
        if self.__used:
            raise RuntimeError("Do not re-use zipFly instances. Recreate it.")
        self.__used = True

    def _apply_remaining_offset(self, data):
        if self._remaining_offset == 0:
            return data
        data_length = len(data)

        # If the offset is greater than or equal to the data length, return empty data
        if self._remaining_offset >= data_length:
            self._remaining_offset -= data_length  # Decrement offset by the length of the skipped data
            self._add_offset(data_length)
            return b''

        # Otherwise, slice data from the offset and reset the offset to 0
        result = data[self._remaining_offset:]
        self._add_offset(self._remaining_offset)
        self._remaining_offset = 0  # Offset is fully applied
        return result
