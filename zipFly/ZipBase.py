import zlib
from typing import List
import zipfile
from zipFly import consts
from zipFly.BaseFile import BaseFile


class ZipBase:

    def __init__(self, files: List[BaseFile], chunksize=8024):
        self.__version = 45
        self.files = files

        self.__offset = 0  # Tracks the current offset within the ZIP archive
        self.__cdir_size = 0
        self.__zip64_end_cdir_offset = 0
        self.__OS_version = 0x03  # UNIX

    def _make_local_file_header(self, file: BaseFile):
        """
        Create local file header for a ZIP64 archive   (4.3.7)
        """

        fields = {
            "signature": consts.LOCAL_FILE_HEADER_SIGNATURE,
            "version": self.__version,
            "flags": file.flags,
            "compression": file.compression_method,
            "mod_time": file.get_mod_time(),
            "mod_date": file.get_mod_date(),
            "crc": 0xFFFFFFFF,  # Placeholder (will be updated in data descriptor)
            "uncomp_size": 0xFFFFFFFF,  # Placeholder (will be updated in data descriptor)
            "comp_size": 0xFFFFFFFF,  # Placeholder (will be updated in data descriptor)
            "fname_len": len(file.file_path_bytes),
            "extra_len": 0  # 0 cuz no extra field is used with local file header
        }

        # Pack the local file header structure
        header = consts.LOCAL_FILE_HEADER_TUPLE(**fields)
        header = consts.LOCAL_FILE_HEADER_STRUCT.pack(*header)
        header += file.file_path_bytes

        return header

    def _make_data_descriptor(self, file: BaseFile):
        """
        Create data descriptor.  (4.3.9)
        """

        fields = {
            "signature": consts.ZIP64_DATA_DESCRIPTOR_SIGNATURE,
            "crc": file.crc & 0xffffffff,  # hack for making CRC unsigned long
            "uncomp_size": file.original_size,
            "comp_size": file.compressed_size,
        }

        descriptor = consts.ZIP64_DATA_DESCRIPTOR_TUPLE(**fields)
        descriptor = consts.ZIP64_DATA_DESCRIPTOR_STRUCT.pack(*descriptor)

        return descriptor

    def _make_cdir_file_header(self, file: BaseFile):
        """
        Create central directory file header for ZIP64 archive.  (4.3.12)
        """
        fields = {
            "signature": consts.CENTRAL_DIR_FILE_HEADER_SIGNATURE,
            "system": self.__OS_version,  # 0x03 - Unix
            "version": self.__version,
            "version_ndd": self.__version,
            "flags": file.flags,
            "compression": file.compression_method,
            "mod_time": file.get_mod_time(),
            "mod_date": file.get_mod_date(),
            "crc": file.crc,
            "comp_size": 0xFFFFFFFF,  # Placeholder (will be updated in zip64 extra field)
            "uncomp_size": 0xFFFFFFFF,  # Placeholder (will be updated in zip64 extra field)
            "fname_len": len(file.file_path_bytes),
            "extra_len": 32,
            "fcomm_len": 0,
            "disk_start": 0,
            "attrs_int": 0,
            "attrs_ext": 0,
            "offset": 0xFFFFFFFF  # Placeholder (will be updated in zip64 extra field)
        }

        # Pack the central directory file header structure
        cdfh = consts.CENTRAL_DIR_FILE_HEADER_TUPLE(**fields)
        cdfh = consts.CENTRAL_DIR_FILE_HEADER_STRUCT.pack(*cdfh)
        cdfh += file.file_path_bytes

        return cdfh

    def _make_zip64_extra_field(self, file: BaseFile):
        """
        Create the ZIP64 extra field.  (4.5.3)
        """
        fields = {
            "signature": consts.ZIP64_EXTRA_FIELD_SIGNATURE,  # ZIP64 extra field format
            "extra_field_size": 28,  # Size of the extra field (28 bytes)
            "size": file.original_size,  # Original uncompressed size
            "compressed_size": file.compressed_size,  # Compressed size
            "offset": file.offset,  # Offset of local file header
            "disk_Start_number": 0  # Disk start number
        }

        extra = consts.ZIP64_EXTRA_FIELD_TUPLE(**fields)
        extra = consts.ZIP64_EXTRA_FIELD_STRUCT.pack(*extra)

        return extra

    def _make_zip64_end_of_cdir_record(self):
        """
        Create the ZIP64 end of central directory record.  (4.3.14)
        """
        fields = {
            "signature": consts.ZIP64_END_OF_CENTRAL_DIR_RECORD_SIGNATURE,
            "size_of_zip64_end_of_central_dir_record": 44,  # 44 bytes for the ZIP64 end of central directory record itself
            "version_made_by": self.__OS_version,  # I have no clue why in the docs it's called 'version made by'. It's actually OS, check(4.4.2)
            "version_needed_to_extract": self.__version,
            "number_of_this_disk": 0,
            "cd_start": 0,
            "cd_entries_this_disk": len(self.files),
            "cd_entries_total": len(self.files),
            "cd_size": self.__cdir_size,
            "cd_offset": self.__offset_to_start_of_central_dir
        }

        cdend = consts.ZIP64_END_OF_CENTRAL_DIR_RECORD_TUPLE(**fields)
        cdend = consts.ZIP64_END_OF_CENTRAL_DIR_RECORD_STRUCT.pack(*cdend)

        return cdend

    def _make_zip64_end_of_cdir_locator(self):
        """
        Create the ZIP64 end of central directory locator.  (4.3.15)
        """
        fields = {
            "signature": consts.ZIP64_END_OF_CENTRAL_DIR_LOCATOR_SIGNATURE,
            "disk_with_zip64_end": 0,
            "zip64_end_offset": self.__offset,
            "total_disks": 1
        }

        locator = consts.ZIP64_END_OF_CENTRAL_DIR_LOCATOR_TUPLE(**fields)

        locator = consts.ZIP64_END_OF_CENTRAL_DIR_LOCATOR_STRUCT.pack(*locator)

        return locator

    def _make_end_of_cdir_record(self):
        """
        Create the end of central directory record.  (4.3.16)
        """
        fields = {
            "signature": consts.END_OF_CENTRAL_DIR_RECORD_SIGNATURE,
            "number_of_this_disk": 0,
            "number_of_disk_with_start_central_dir": 0,
            "total_entries_on_this_disk": len(self.files),
            "total_entries_total": len(self.files),
            "central_directory_size": 0xFFFFFFFF,
            "offset_of_central_directory": 0xFFFFFFFF,
            # "offset_of_central_directory": self.__offset_to_start_of_central_dir,  # Corrected to use the proper offset
            "comment_length": 0  # No comment
        }

        eocd = consts.END_OF_CENTRAL_DIR_RECORD_TUPLE(**fields)
        eocd = consts.END_OF_CENTRAL_DIR_RECORD_STRUCT.pack(*eocd)

        return eocd

    def get_offset(self):
        return self.__offset

    def add_offset(self, value):
        self.__offset += value

    def _stream_single_file(self, file: BaseFile):
        """
        stream single zip file with header and descriptor at the end
        """
        yield self._make_local_file_header(file)

        yield from file.generate_processed_file_data()

        yield self._make_data_descriptor(file)

    def _make_end_structures(self):
        """
        Make zip64 end structures, which include:
            central directory file header for every file,
            zip64 extra fields for every file,
            zip64 end of central dir record,
            zip64 end of central dir locator
            end of central dir record
        """

        # Stream central directory entries
        self.__offset_to_start_of_central_dir = self.__offset

        for file in self.files:
            chunk = self._make_cdir_file_header(file)
            chunk += self._make_zip64_extra_field(file)
            self.__cdir_size += len(chunk)
            self.__offset += len(chunk)
            yield chunk

        yield self._make_zip64_end_of_cdir_record()

        yield self._make_zip64_end_of_cdir_locator()

        yield self._make_end_of_cdir_record()

