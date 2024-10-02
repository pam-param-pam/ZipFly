from typing import Generator, AsyncGenerator

from zipFly import BaseFile
from zipFly.ZipBase import ZipBase

class ZipFly(ZipBase):

    def calculate_archive_size(self) -> int:
        LOCAL_FILE_HEADER_SIZE = 30
        DATA_DESCRIPTOR_SIZE = 24
        CENTRAL_DIR_HEADER_SIZE = 46
        ZIP64_EXTRA_FIELD_SIZE = 28
        ZIP64_END_OF_CDIR_RECORD_SIZE = 56
        ZIP64_END_OF_CDIR_LOCATOR_SIZE = 20
        END_OF_CDIR_RECORD_CD_RECORD_SIZE = 22

        total_size = 0

        for file in self.files:
            local_file_header_size = LOCAL_FILE_HEADER_SIZE + len(file.file_path_bytes)

            total_size += local_file_header_size
            total_size += file.size
            total_size += DATA_DESCRIPTOR_SIZE

            central_directory_header_size = CENTRAL_DIR_HEADER_SIZE + len(file.file_path_bytes) + ZIP64_EXTRA_FIELD_SIZE

            total_size += central_directory_header_size

        total_size += ZIP64_END_OF_CDIR_RECORD_SIZE
        total_size += ZIP64_END_OF_CDIR_LOCATOR_SIZE
        total_size += END_OF_CDIR_RECORD_CD_RECORD_SIZE

        return total_size

    def _make_end_structures(self) -> Generator[bytes, None, None]:
        """
        Make zip64 end structures, which include:
            central directory file header for every file,
            zip64 extra field for every file,
            zip64 end of central dir record,
            zip64 end of central dir locator
            end of central dir record
        """
        # Save offset to start of central dir for zip64 end of cdir record
        self._offset_to_start_of_central_dir = self._get_offset()

        # Stream central directory entries
        for file in self.files:
            chunk = self._make_cdir_file_header(file)
            chunk += self._make_zip64_extra_field(file)
            self._cdir_size = len(chunk)
            self._add_offset(len(chunk))

            yield chunk

        yield self._make_zip64_end_of_cdir_record()

        yield self._make_zip64_end_of_cdir_locator()

        yield self._make_end_of_cdir_record()

    async def _async_stream_single_file(self, file: BaseFile) -> AsyncGenerator[bytes, None]:

        yield self._make_local_file_header(file)

        async for chunk in file.async_generate_processed_file_data():
            yield chunk

        yield self._make_data_descriptor(file)

    async def async_stream(self) -> AsyncGenerator[bytes, None]:
        # stream files
        for file in self.files:

            file.offset = self._get_offset()
            async for chunk in self._async_stream_single_file(file):
                self._add_offset(len(chunk))
                yield chunk

        # stream zip structures
        for chunk in self._make_end_structures():
            yield chunk

    def stream(self) -> Generator[bytes, None, None]:
        # stream files
        for file in self.files:
            print("offset")
            print(self._get_offset())
            file.offset = self._get_offset()
            for chunk in self._stream_single_file(file):
                self._add_offset(len(chunk))
                yield chunk

        # stream zip structures
        for chunk in self._make_end_structures():
            yield chunk

    def _stream_single_file(self, file: BaseFile) -> Generator[bytes, None, None]:
        """
        stream single zip file with header and descriptor at the end.
        """
        yield self._make_local_file_header(file)

        yield from file.generate_processed_file_data()

        yield self._make_data_descriptor(file)



