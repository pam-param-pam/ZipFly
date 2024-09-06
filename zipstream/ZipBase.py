import struct
import time
import zlib
from typing import List

from zipstream import consts
from zipstream.BaseFile import BaseFile


class Compressor:
    def __init__(self, file: BaseFile):
        self.crc = 0
        self.o_size = self.c_size = 0
        if file.compression_method is None:
            self.process = self._process_through
            self.tail = self._no_tail
        elif file.compression_method == 'deflate':
            self.compr = zlib.compressobj(5, zlib.DEFLATED, -15)
            self.process = self._process_deflate
            self.tail = self._tail_deflate

    # no compression
    def _process_through(self, chunk):
        self.o_size += len(chunk)
        self.c_size = self.o_size
        self.crc = zlib.crc32(chunk, self.crc)
        return chunk

    def _no_tail(self):
        return b''

    # deflate compression
    def _process_deflate(self, chunk):
        self.o_size += len(chunk)
        self.crc = zlib.crc32(chunk, self.crc)
        chunk = self.compr.compress(chunk)
        self.c_size += len(chunk)
        return chunk

    def _tail_deflate(self):
        chunk = self.compr.flush(zlib.Z_FINISH)
        self.c_size += len(chunk)
        return chunk

    # after processing counters and crc
    def state(self):
        return self.crc, self.o_size, self.c_size


class ZipBase:

    def __init__(self, files: List[BaseFile], chunksize=8024):
        self.__version = 45
        self.files = files
        self.chunksize = chunksize

        self.offset = 0  # Tracks the current offset within the ZIP archive
        self.central_directory = []
        self.local_headers = []
        self.central_directory_size = 0
        self.total_entries = 0
        self.__cdir_size = 0

    def _make_local_file_header(self, file: BaseFile):
        """
        Create the local file header for a ZIP64 archive, with placeholder sizes
        and an extra field for the ZIP64 format.
        """


        # Set the fields for the local file header
        fields = {
            "signature": consts.LOCAL_FILE_SIGNATURE,
            "version": self.__version,  # ZIP64 format version, typically 45
            "flags": 0b00001000,  # flag about using data descriptor is always on
            "compression": 0,  # no compresion
            "mod_time": file.get_mod_time(),
            "mod_date": file.get_mod_date(),
            "crc": 0xFFFFFFFF,  # Placeholder CRC32 for now (to be updated after streaming)
            "uncomp_size": 0xFFFFFFFF,
            "comp_size": 0xFFFFFFFF,
            "fname_len": len(file.name_path),
            "extra_len": 0  # 28 bytes for ZIP64 extra field (8 bytes each for sizes and offset, 4 bytes for disk start number)
        }

        # Pack the local file header structure
        head = consts.LOCAL_FILE_TUPLE(**fields)
        head = consts.LOCAL_FILE_STRUCT.pack(*head)
        head += file.name_path

        # # ZIP64 extra field
        # zip64_extra_field = struct.pack(
        #     '<HHQQQI',  # ZIP64 extra field format
        #     0x0001,  # ZIP64 extra field ID
        #     32,  # Size of the extra field (24 bytes)
        #     0xFFFFFFFF,  # Placeholder for original uncompressed size (to be filled later)
        #     0xFFFFFFFF,  # Placeholder for compressed size (to be filled later)
        #     0xFFFFFFFF,  # Placeholder for local file header offset (to be filled later)
        #     0  # Disk start number (often 0 for single-disk ZIP archives)
        # )
        # head += zip64_extra_field

        return head

    def _make_data_descriptor(self, file: BaseFile, crc, org_size, compr_size):
        """
        Create file descriptor.
        This function also updates size and crc fields of file_struct
        """
        # hack for making CRC unsigned long

        # updating values
        file.crc = crc & 0xffffffff
        file.org_size = org_size
        file.compr_size = compr_size



        fields = {"crc": file.crc,
                  "uncomp_size": file.org_size,
                  "comp_size": file.compr_size,
                  }
        descriptor = consts.DATA_DESCRIPTOR_TUPLE(**fields)
        descriptor = consts.DATA_DESCRIPTOR_STRUCT64.pack(*descriptor)

        descriptor = consts.DATA_DESCRIPTOR_SIGNATURE + descriptor

        return descriptor

    def _stream_single_file(self, file: BaseFile):
        """
        stream single zip file with header and descriptor at the end
        """
        yield self._make_local_file_header(file)
        pcs = Compressor(file)
        for chunk in file.generate_file_data():
            chunk = pcs.process(chunk)
            if len(chunk) > 0:
                yield chunk
        chunk = pcs.tail()
        if len(chunk) > 0:
            yield chunk

        yield self._make_data_descriptor(file, *pcs.state())

    def _make_cdir_file_header(self, file: BaseFile):
        """
        Create central directory file header for ZIP64 archive.
        """
        print(file.crc)
        print(file.org_size)
        print(file.compr_size)
        print(file.offset)
        # Create ZIP64 extra field
        zip64_extra_field = struct.pack(
            '<HHQQQL',  # ZIP64 extra field format
            0x0001,  # ZIP64 extra field ID
            28,  # Size of the extra field (28 bytes)
            file.org_size,  # Original uncompressed size
            file.compr_size,  # Compressed size
            file.offset,  # Offset of local file header
            0  # Disk start number
        )
        extra_len = len(zip64_extra_field)

        # Set the fields for the central directory file header
        fields = {
            "signature": consts.CENTRAL_DIR_FILE_HEADER_SIGNATURE,
            "system": 0x03,  # 0x03 - Unix
            "version": self.__version,
            "version_ndd": self.__version,
            "flags": 0b00001000,  # flag about using data descriptor is always on
            "compression": 0,  # no compr
            "mod_time": file.get_mod_time(),
            "mod_date": file.get_mod_date(),
            "crc": file.crc,
            "comp_size": 0xFFFFFFFF,
            "uncomp_size": 0xFFFFFFFF,
            "fname_len": len(file.name_path),
            "extra_len": 32,  # Length of the ZIP64 extra field
            "fcomm_len": 0,  # Comment length
            "disk_start": 0,
            "attrs_int": 0,
            "attrs_ext": 0,
            "offset": 0xFFFFFFFF   # Offset in central directory
        }

        # Pack the central directory file header structure
        cdfh = consts.CENTRAL_DIR_LOCAL_FILE_TUPLE(**fields)
        cdfh = consts.CENTRAL_DIR_LOCAL_FILE_STRUCT.pack(*cdfh)
        cdfh += file.name_path
        cdfh += zip64_extra_field  # Append ZIP64 extra field if necessary

        return cdfh

    def _make_cdend(self):
        """
        Create the ZIP64 end of central directory record.
        """
        # Prepare the fields for the ZIP64 end of central directory record
        fields = {
            "signature": consts.ZIP64_CENTRAL_DIR_END_SIGNATURE,
            "size_of_zip64_end_of_central_dir_record": 44 + self.__cdir_size,  # 44 bytes for the ZIP64 end of central directory record itself
            "version_made_by": 0x03,  # UNIX
            "version_needed_to_extract": self.__version,
            "number_of_this_disk": 0,
            "cd_start": 0,  # Number of the disk with the start of the central directory
            "cd_entries_this_disk": len(self.files),
            "cd_entries_total": len(self.files),
            "cd_size": self.__cdir_size,
            "cd_offset": self.offset
        }

        # Pack the fields into the ZIP64 end of central directory record format
        cdend = consts.ZIP64_CENTRAL_DIR_END_TUPLE(**fields)
        cdend = consts.ZIP64_CENTRAL_DIR_END_STRUCT.pack(*cdend)

        return cdend

    def _make_zip64_locator(self):
        """
        Create the ZIP64 end of central directory locator.
        """
        fields = {
            "signature": 0x07064b50,  # ZIP64 end of central directory locator signature
            "disk_with_zip64_end": 0,  # Number of the disk with the start of the ZIP64 end of central directory
            "zip64_end_offset": self.__zip64_end_cdir_offset,
            "total_disks": 1  # Total number of disks
        }

        # Pack the fields into the ZIP64 end of central directory locator format
        locator = struct.pack('<LQLL', fields["signature"], fields["disk_with_zip64_end"], fields["zip64_end_offset"], fields["total_disks"])

        return locator

    def _make_end_structures(self):
        """
        Central directory and end of central directory structures are saved at the end of zip file
        """
        # Stream central directory entries
        for file in self.files:
            chunk = self._make_cdir_file_header(file)
            self.__cdir_size += len(chunk)
            yield chunk

        # Stream ZIP64 end of central directory
        self.__zip64_end_cdir_offset = self.offset  # Set the offset before creating the ZIP64 end of central directory
        yield self._make_cdend()

        # Stream ZIP64 end of central directory locator
        self.__zip64_locator_offset = self.offset  # Set the offset before creating the ZIP64 end of central directory locator
        yield self._make_zip64_locator()

    def _make_end_of_central_directory(self):
        """
        Create the end of central directory record.
        """
        # Set the fields for the end of central directory record
        fields = {
            "signature": 0x06054b50,  # End of central directory record signature
            "number_of_this_disk": 0,
            "number_of_disk_with_start_central_dir": 0,
            "total_entries_on_this_disk": len(self.files),
            "total_entries_total": len(self.files),
            "central_directory_size": self.__cdir_size,
            "offset_of_central_directory": self.__zip64_end_cdir_offset,  # Corrected to use the proper offset
            "comment_length": 0  # No comment
        }
        signature_bytes = fields["signature"].to_bytes(4, 'little')

        # Pack the end of central directory record structure
        eocd = struct.pack(
            '<4sHHHHLLH',
            signature_bytes,
            fields["number_of_this_disk"],
            fields["number_of_disk_with_start_central_dir"],
            fields["total_entries_on_this_disk"],
            fields["total_entries_total"],
            fields["central_directory_size"],
            fields["offset_of_central_directory"],
            fields["comment_length"]
        )

        return eocd

class ZipFly(ZipBase):

    def stream(self):
        for file in self.files:
            file.offset = self.offset
            for chunk in self._stream_single_file(file):
                self.offset += len(chunk)
                yield chunk

        # stream zip structures
        for chunk in self._make_end_structures():
            yield chunk
        yield self._make_end_of_central_directory()
