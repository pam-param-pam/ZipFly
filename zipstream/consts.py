from collections import namedtuple
import struct

# ZIP CONSTANTS
ZIP32_VERSION = 20
ZIP64_VERSION = 45
ZIP32_LIMIT = (1 << 31) - 1
UTF8_FLAG = 0x800  # utf-8 filename encoding flag


# ZIP COMPRESSION METHODS
COMPRESSION_STORE = 0
COMPRESSION_DEFLATE = 8
COMPRESSION_BZIP2 = 12
COMPRESSION_LZMA = 14


# LOCAL FILE HEADER
LOCAL_FILE_HEADER_SIGNATURE = b'\x50\x4b\x03\x04'
LOCAL_FILE_HEADER_STRUCT = struct.Struct(b"<4sHHHHHLLLHH")
LOCAL_FILE_HEADER_TUPLE = namedtuple("fileheader",
                                     ("signature", "version", "flags",
                                      "compression", "mod_time", "mod_date",
                                      "crc", "comp_size", "uncomp_size",
                                      "fname_len", "extra_len"))


# ZIP64 EXTRA FIELD
ZIP64_EXTRA_FIELD_SIGNATURE = b'\x01\x00'
ZIP64_EXTRA_FIELD_STRUCT = struct.Struct(b"<2sHQQQL")
ZIP64_EXTRA_FIELD_TUPLE = namedtuple("extra", ("signature", "extra_field_size", "size", "compressed_size", "offset", "disk_Start_number"))


# FILE DESCRIPTOR
ZIP64_DATA_DESCRIPTOR_SIGNATURE = b'\x50\x4b\x07\x08'
ZIP64_DATA_DESCRIPTOR_STRUCT = struct.Struct(b"<4sLQQ")
ZIP64_DATA_DESCRIPTOR_TUPLE = namedtuple("filecrc", ("signature", "crc", "comp_size", "uncomp_size"))


# CENTRAL DIRECTORY FILE HEADER
CENTRAL_DIR_FILE_HEADER_SIGNATURE = b'\x50\x4b\x01\x02'
CENTRAL_DIR_FILE_HEADER_STRUCT = struct.Struct(b"<4sBBHHHHHLLLHHHHHLL")
CENTRAL_DIR_FILE_HEADER_TUPLE = namedtuple("cdfileheader",
                                           ("signature", "system", "version", "version_ndd", "flags",
                                           "compression", "mod_time", "mod_date", "crc",
                                           "comp_size", "uncomp_size", "fname_len", "extra_len",
                                           "fcomm_len", "disk_start", "attrs_int", "attrs_ext", "offset"))

# ZIP64 END OF CENTRAL DIRECTORY RECORD
ZIP64_END_OF_CENTRAL_DIR_RECORD_SIGNATURE = b'\x50\x4b\x06\x06'
ZIP64_END_OF_CENTRAL_DIR_RECORD_STRUCT = struct.Struct(b"<4sQHHIIQQQQ")
ZIP64_END_OF_CENTRAL_DIR_RECORD_TUPLE = namedtuple("zip64end",
                                                   ("signature", "size_of_zip64_end_of_central_dir_record", "version_made_by", "version_needed_to_extract",
                                          "number_of_this_disk", "cd_start", "cd_entries_this_disk", "cd_entries_total",
                                          "cd_size", "cd_offset"))


# END OF CENTRAL DIRECTORY LOCATOR
END_OF_CENTRAL_DIR_LOCATOR_SIGNATURE = b'\x50\x4b\x07\x08'
END_OF_CENTRAL_DIR_LOCATOR_STRUCT = struct.Struct(b"<4sQLL")
END_OF_CENTRAL_DIR_LOCATOR_TUPLE = namedtuple("eocdlocator",
                                              ("signature", "disk_with_zip64_end", "zip64_end_offset", "total_disks"))


# END OF CENTRAL DIRECTORY RECORD
END_OF_CENTRAL_DIR_RECORD_SIGNATURE = b'P\x4b\x05\x06'
END_OF_CENTRAL_DIR_RECORD_STRUCT = struct.Struct(b"<4sHHHHLLH")
END_OF_CENTRAL_DIR_RECORD_TUPLE = namedtuple("eocdlocator", ("signature", "number_of_this_disk", "number_of_disk_with_start_central_dir",
                                                             "total_entries_on_this_disk", "total_entries_total",
                                                             "central_directory_size", "offset_of_central_directory",
                                                             "comment_length"))
