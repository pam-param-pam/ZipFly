"""Run tests of ZipFly."""
import re
import struct
import time
import zipfile
import zlib

# Need to also have https://pypi.org/project/pytest-asyncio/ installed
# The 4GB tests are kind of slow, this can help if you have enough memory.
# Install this https://pypi.org/project/pytest-xdist/ and then
# `pytest -n auto`
import pytest

from src.zipFly import GenFile, LocalFile, ZipFly, consts
from src.zipFly.EmptyFolder import EmptyFolder
from tests.test_utils import lorem_ipsum_generator, lorem_ipsum, single_archive_size, lorem_ipsum_generator_async, multifile_archive_size, generate_data_async, \
    single_archive_size_with_extra_field


@pytest.mark.asyncio
async def test_GenFile_multiple_files_async(tmp_path):
    """Test async ZIP with multiple small files (~10KB each)."""
    n = 10
    chunk = b"x" * 1024  # 1KB
    chunks_per_file = 10
    expected_content = chunk * chunks_per_file

    files = []
    for i in range(n):
        generator_func = generate_data_async(chunk, chunks_per_file)
        file = GenFile(
            name=f"file_{i}.txt",
            generator=generator_func(),
            modification_time=time.time(),
            compression_method=consts.COMPRESSION_DEFLATE,
        )
        files.append(file)

    zip_fly = ZipFly(files)
    zip_path = tmp_path / "multi_file_async.zip"

    with zip_path.open("wb") as fp:
        async for zip_chunk in zip_fly.async_stream():
            fp.write(zip_chunk)

    with zipfile.ZipFile(zip_path) as zfp:
        namelist = zfp.namelist()
        assert len(namelist) == n

        for i in range(n):
            fname = f"file_{i}.txt"
            assert fname in namelist
            with zfp.open(fname) as tfp:
                data = tfp.read()
                assert data == expected_content

def test_GenFile_COMPRESSION_DEFLATE(tmp_path):
    """Test GenFile with compression."""
    file1 = GenFile(
        name="lorem_ipsum.txt",
        generator=lorem_ipsum_generator(),
        modification_time=time.time(),
        compression_method=consts.COMPRESSION_DEFLATE,
    )
    zip_fly = ZipFly([file1])

    zip_path = tmp_path / "deflate.zip"
    with zip_path.open("wb") as fp:
        for chunk in zip_fly.stream():
            fp.write(chunk)

    with zipfile.ZipFile(zip_path) as zfp, zfp.open("lorem_ipsum.txt") as tfp:
        out = tfp.read()

    assert lorem_ipsum == out


@pytest.mark.asyncio
async def test_GenFile_COMPRESSION_DEFLATE_async(tmp_path):
    """Test GenFile with compression (async)."""
    file1 = GenFile(
        name="lorem_ipsum.txt",
        generator=lorem_ipsum_generator_async(),
        modification_time=time.time(),
        compression_method=consts.COMPRESSION_DEFLATE,
    )
    zip_fly = ZipFly([file1])

    zip_path = tmp_path / "deflate_async.zip"
    with zip_path.open("wb") as fp:
        async for chunk in zip_fly.async_stream():
            fp.write(chunk)

    with zipfile.ZipFile(zip_path) as zfp, zfp.open("lorem_ipsum.txt") as tfp:
        out = tfp.read()

    assert lorem_ipsum == out


def test_GenFile_NO_COMPRESSION(tmp_path):
    """Test GenFile without compression."""
    file1 = GenFile(
        name="lorem_ipsum.txt",
        generator=lorem_ipsum_generator(),
        modification_time=time.time(),
        size=len(lorem_ipsum),
    )
    zip_fly = ZipFly([file1])

    zip_path = tmp_path / "nocompress.zip"
    with zip_path.open("wb") as fp:
        for chunk in zip_fly.stream():
            fp.write(chunk)

    with zipfile.ZipFile(zip_path) as zfp, zfp.open("lorem_ipsum.txt") as tfp:
        out = tfp.read()

    assert lorem_ipsum == out
    assert zip_fly.calculate_archive_size() == single_archive_size


@pytest.mark.asyncio
async def test_GenFile_NO_COMPRESSION_async(tmp_path):
    """Test GenFile without compression (async)."""
    file1 = GenFile(
        name="lorem_ipsum.txt",
        generator=lorem_ipsum_generator_async(),
        modification_time=time.time(),
        size=len(lorem_ipsum),
    )
    zip_fly = ZipFly([file1])

    zip_path = tmp_path / "nocompress_async.zip"
    with zip_path.open("wb") as fp:
        async for chunk in zip_fly.async_stream():
            fp.write(chunk)

    with zipfile.ZipFile(zip_path) as zfp, zfp.open("lorem_ipsum.txt") as tfp:
        out = tfp.read()

    assert lorem_ipsum == out
    assert zip_fly.calculate_archive_size() == single_archive_size


def test_LocalFile_COMPRESSION(tmp_path):
    """Test LocalFile with compression."""
    input_path = tmp_path / "lorem_input.txt"
    input_path.write_bytes(lorem_ipsum)

    file1 = LocalFile(
        name="lorem_ipsum.txt",
        file_path=input_path,
        compression_method=consts.COMPRESSION_DEFLATE,
    )
    zip_fly = ZipFly([file1])

    zip_path = tmp_path / "compressed.zip"
    with zip_path.open("wb") as fp:
        for chunk in zip_fly.stream():
            fp.write(chunk)

    with zipfile.ZipFile(zip_path) as zfp, zfp.open("lorem_ipsum.txt") as tfp:
        out = tfp.read()

    assert lorem_ipsum == out
    assert zip_fly.calculate_archive_size() == single_archive_size


@pytest.mark.asyncio
async def test_LocalFile_COMPRESSION_async(tmp_path):
    """Test LocalFile with compression (async)."""
    input_path = tmp_path / "lorem_input.txt"
    input_path.write_bytes(lorem_ipsum)

    file1 = LocalFile(
        name="lorem_ipsum.txt",
        file_path=input_path,
        compression_method=consts.COMPRESSION_DEFLATE,
    )
    zip_fly = ZipFly([file1])

    zip_path = tmp_path / "compressed_async.zip"
    with zip_path.open("wb") as fp:
        async for chunk in zip_fly.async_stream():
            fp.write(chunk)

    with zipfile.ZipFile(zip_path) as zfp, zfp.open("lorem_ipsum.txt") as tfp:
        out = tfp.read()

    assert lorem_ipsum == out
    assert zip_fly.calculate_archive_size() == single_archive_size


def test_LocalFile_NO_COMPRESSION(tmp_path):
    """Test LocalFile without compression."""
    input_path = tmp_path / "lorem_input.txt"
    input_path.write_bytes(lorem_ipsum)

    file1 = LocalFile(
        name="lorem_ipsum.txt",
        file_path=input_path,
    )
    zip_fly = ZipFly([file1])

    zip_path = tmp_path / "nocompress_local.zip"
    with zip_path.open("wb") as fp:
        for chunk in zip_fly.stream():
            fp.write(chunk)

    with zipfile.ZipFile(zip_path) as zfp, zfp.open("lorem_ipsum.txt") as tfp:
        out = tfp.read()
        for info in zfp.infolist():
            print(f"{info.filename}: CRC={hex(info.CRC)}")

    assert lorem_ipsum == out
    assert zip_fly.calculate_archive_size() == single_archive_size_with_extra_field


@pytest.mark.asyncio
async def test_LocalFile_NO_COMPRESSION_async(tmp_path):
    """Test LocalFile without compression (async)."""
    input_path = tmp_path / "lorem_input.txt"
    input_path.write_bytes(lorem_ipsum)

    file1 = LocalFile(
        name="lorem_ipsum.txt",
        file_path=input_path,
    )
    zip_fly = ZipFly([file1])

    zip_path = tmp_path / "nocompress_local_async.zip"
    with zip_path.open("wb") as fp:
        async for chunk in zip_fly.async_stream():
            fp.write(chunk)

    with zipfile.ZipFile(zip_path) as zfp, zfp.open("lorem_ipsum.txt") as tfp:
        out = tfp.read()

    assert lorem_ipsum == out
    assert zip_fly.calculate_archive_size() == single_archive_size_with_extra_field


def test_multifile_archive(tmp_path):
    """Test adding multiple files to an archive."""
    n_files = 5
    input_paths = []
    for i in range(n_files):
        path = tmp_path / f"lorem_{i}.txt"
        path.write_bytes(lorem_ipsum)
        input_paths.append(path)

    files = [
        LocalFile(
            name=f"lorem_ipsum_{i}.txt",
            file_path=path,
            compression_method=consts.COMPRESSION_DEFLATE,
        )
        for i, path in enumerate(input_paths)
    ]
    zip_fly = ZipFly(files)

    zip_path = tmp_path / "multifile.zip"
    with zip_path.open("wb") as fp:
        for chunk in zip_fly.stream():
            fp.write(chunk)

    outs = []
    with zipfile.ZipFile(zip_path) as zfp:
        for zname in zfp.filelist:
            with zfp.open(zname.filename) as tfp:
                outs.append(tfp.read())

    for out in outs:
        assert out == lorem_ipsum

    assert zip_fly.calculate_archive_size() == multifile_archive_size


@pytest.mark.asyncio
async def test_multifile_archive_async(tmp_path):
    """Test adding multiple files to an archive (async version) using tmp_path."""
    n_files = 5
    outnames = []

    # Create temp files using tmp_path
    for i in range(n_files):
        temp_file = tmp_path / f"lorem_{i}.txt"
        temp_file.write_bytes(lorem_ipsum)
        outnames.append(temp_file)

    # Prepare LocalFile objects
    files = [
        LocalFile(
            name=f"lorem_ipsum_{i}.txt",
            file_path=str(path),
            compression_method=consts.COMPRESSION_DEFLATE,
        )
        for i, path in enumerate(outnames)
    ]

    zip_fly = ZipFly(files)
    archive_path = tmp_path / "test_archive.zip"

    # Stream zip archive asynchronously
    with archive_path.open("wb") as f_out:
        async for chunk in zip_fly.async_stream():
            f_out.write(chunk)

    assert zip_fly.calculate_archive_size() == multifile_archive_size

    # Validate zip content
    outs = []
    with zipfile.ZipFile(archive_path) as zfp:
        for zname in zfp.filelist:
            with zfp.open(zname.filename) as tfp:
                outs.append(tfp.read())

    for out in outs:
        assert out == lorem_ipsum


def test_zipfly_stream_reuse_raises():
    """Ensure ZipFly raises an error when .stream() is reused."""
    file1 = GenFile(
        name="lorem_ipsum.txt",
        generator=lorem_ipsum_generator(),
        modification_time=time.time(),
        size=len(lorem_ipsum),
    )
    zip_fly = ZipFly([file1])

    for _ in zip_fly.stream():
        break

    with pytest.raises(Exception):
        for _ in zip_fly.stream():
            break


STOP_BYTE_VALUES = list(range(0, 2001, 50))

@pytest.mark.asyncio
@pytest.mark.parametrize("STOP_BYTE", STOP_BYTE_VALUES)
@pytest.mark.parametrize("file_cls", ["local", "gen"])
async def test_zipfly_resumable_async(tmp_path, STOP_BYTE, file_cls):
    out_file = tmp_path / f"{file_cls}_{STOP_BYTE}_resumed.zip"
    byte_offset = 0
    file_count = 2
    files = []

    # Create input files
    for i in range(file_count):
        name = f"lorem_{i}.txt"
        if file_cls == "local":
            data_path = tmp_path / f"file_{i}.txt"
            data_path.write_bytes(lorem_ipsum)
            file = LocalFile(
                file_path=data_path,
                name=name,
            )
        elif file_cls == "gen":
            file = GenFile(
                name=name,
                generator=lorem_ipsum_generator_async(),
                size=len(lorem_ipsum),
                modification_time=time.time(),
                crc=zlib.crc32(lorem_ipsum)
            )
        else:
            raise ValueError("Unsupported file class")
        files.append(file)

    zipFly1 = ZipFly(files)

    # If using GenFile, recreate generator objects for the resume ZipFly
    if file_cls == "gen":
        files_resume = [
            GenFile(
                name=f"lorem_{i}.txt",
                generator=lorem_ipsum_generator_async(),
                size=len(lorem_ipsum),
                modification_time=time.time(),
                crc=zlib.crc32(lorem_ipsum)
            )
            for i in range(file_count)
        ]
    else:
        files_resume = files

    zipFly2 = ZipFly(files_resume, byte_offset=STOP_BYTE)

    # Pause: write first part of the archive
    async def pause_zip_async():
        nonlocal byte_offset
        with open(out_file, "wb") as f_out:
            async for chunk in zipFly1.async_stream():
                remaining = STOP_BYTE - byte_offset
                if remaining <= 0:
                    break
                if len(chunk) > remaining:
                    chunk = chunk[:remaining]
                f_out.write(chunk)
                byte_offset += len(chunk)
                if byte_offset >= STOP_BYTE:
                    break

    # Resume: continue writing from STOP_BYTE
    async def resume_zip_async():
        with open(out_file, "ab") as f_out:
            async for chunk in zipFly2.async_stream():
                f_out.write(chunk)

    await pause_zip_async()
    await resume_zip_async()

    # Validate archive
    with zipfile.ZipFile(out_file) as zfp:
        for i in range(file_count):
            file_name = f"lorem_{i}.txt"
            info = zfp.getinfo(file_name)
            assert info.file_size == len(lorem_ipsum)
            with zfp.open(file_name) as tfp:
                content = tfp.read()
                assert content == lorem_ipsum


@pytest.mark.asyncio
@pytest.mark.parametrize("file_cls", ["local", "gen"])
async def test_zipfly_resumable_async_offset_exceeds_archive(tmp_path, file_cls):
    file_count = 2
    files = []

    # Create input files
    for i in range(file_count):
        name = f"lorem_{i}.txt"
        if file_cls == "local":
            data_path = tmp_path / f"file_{i}.txt"
            data_path.write_bytes(lorem_ipsum)
            file = LocalFile(
                file_path=data_path,
                name=name,
            )
        elif file_cls == "gen":
            file = GenFile(
                name=name,
                generator=lorem_ipsum_generator_async(),
                size=len(lorem_ipsum),
                modification_time=time.time(),
                crc=zlib.crc32(lorem_ipsum)
            )
        else:
            raise ValueError("Unsupported file class")
        files.append(file)

    zipFly = ZipFly(files)
    archive_size = zipFly.calculate_archive_size()
    invalid_offset = archive_size + 100  # wrong offset

    # Prepare ZipFly with fresh generator objects if GenFile
    if file_cls == "gen":
        files_resume = [
            GenFile(
                name=f"lorem_{i}.txt",
                generator=lorem_ipsum_generator_async(),
                size=len(lorem_ipsum),
                modification_time=time.time(),
                crc=zlib.crc32(lorem_ipsum)
            )
            for i in range(file_count)
        ]
    else:
        files_resume = files

    zipFly_resume = ZipFly(files_resume, byte_offset=invalid_offset)

    with pytest.raises(ValueError):
        async for _ in zipFly_resume.async_stream():
            pass  # Should not reach here


@pytest.mark.asyncio
async def test_genfile_reuse_raises():
    file = GenFile(
        name="test.txt",
        generator=lorem_ipsum_generator_async(),  # async generator
        size=len(lorem_ipsum),
        modification_time=time.time(),
        crc=zlib.crc32(lorem_ipsum),
    )

    zipFly = ZipFly([file])

    # First usage should succeed
    chunks = []
    async for chunk in zipFly.async_stream():
        chunks.append(chunk)

    # Reuse same GenFile — should raise (due to exhausted generator)
    zipFly_reuse = ZipFly([file])

    with pytest.raises(RuntimeError, match="Do not re-use file instances. Recreate it."):
        async for _ in zipFly_reuse.async_stream():
            pass


@pytest.mark.asyncio
async def test_zipfly_instance_reuse_raises():
    file = GenFile(generator=lorem_ipsum_generator_async(), name="UwU.txt")
    zipFly = ZipFly([file])

    # First use should succeed
    async for _ in zipFly.async_stream():
        break  # stream at least once

    # Reuse should raise error (state was consumed)
    with pytest.raises(RuntimeError, match="Do not re-use zipFly instances. Recreate it."):
        async for _ in zipFly.async_stream():
            pass


@pytest.mark.asyncio
async def test_zipfly_wrong_size_raises():
    async def broken_gen():
        yield b'abc'

    file = GenFile(generator=broken_gen(), name="broken_size.txt", size=5)
    zipFly = ZipFly([file])

    with pytest.raises(RuntimeError, match=re.escape("Size(5) != streamed size(3)")):
        async for _ in zipFly.async_stream():
            pass


@pytest.mark.asyncio
async def test_zipfly_resumable_genfile_wrong_crc_raises(tmp_path):
    """This will be raised"""
    file_count = 2
    files = []

    # Create input files
    for i in range(file_count):
        file = GenFile(
            name=f"lorem_{i}.txt",
            generator=lorem_ipsum_generator_async(),
            size=len(lorem_ipsum),
            modification_time=time.time(),
            crc=1
        )

        files.append(file)

    zipFly = ZipFly(files)

    with pytest.raises(RuntimeError, match=re.escape(f"Crc(1) != streamed crc({zlib.crc32(lorem_ipsum)})")):
        async for _ in zipFly.async_stream():
            pass

def test_renaming_duplicated_file_names(tmp_path):
    file_path = tmp_path / "lorem_input.txt"
    file_path.write_bytes(lorem_ipsum)

    file1 = LocalFile(
        file_path=file_path,
        name="same_name.txt"
    )
    file2 = LocalFile(
        file_path=file_path,
        name="same_name.txt"
    )

    file3 = LocalFile(
        file_path=file_path,
        name="same_name1.txt"
    )

    file4 = LocalFile(
        file_path=file_path,
        name="same_name (1).txt"
    )

    zip_path = tmp_path / "duplicate_names.zip"
    zipfly = ZipFly([file1, file2, file3, file4])

    with open(zip_path, "wb") as f:
        for chunk in zipfly.stream():
            f.write(chunk)

    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        assert "same_name.txt" in names
        assert "same_name (1).txt" in names
        assert "same_name1.txt" in names
        assert "same_name (1) (1).txt" in names


@pytest.mark.parametrize("file_cls", ["gen", "local"])
def test_modification_time(tmp_path, file_cls):
    test_time = time.time()
    test_time_rounded = int(test_time)

    name = "file.txt"

    if file_cls == "gen":
        file = GenFile(
            name=name,
            generator=lorem_ipsum_generator(),
            size=len(lorem_ipsum),
            modification_time=test_time,
            crc=zlib.crc32(lorem_ipsum)
        )
    else:
        file_path = tmp_path / name
        file_path.write_bytes(lorem_ipsum)
        file = LocalFile(
            file_path=file_path,
            name=name,
        )

    zip_path = tmp_path / f"{file_cls}_mtime.zip"
    zipfly = ZipFly([file])

    with open(zip_path, "wb") as f:
        for chunk in zipfly.stream():
            f.write(chunk)

    with zipfile.ZipFile(zip_path) as zf:
        info = zf.getinfo(name)
        zip_time = time.mktime(info.date_time + (0, 0, -1))
        # Round both for comparison due to zip format limitations (2s resolution)
        assert abs(round(zip_time) - round(test_time_rounded)) <= 2


def test_EmptyFolder_creates_empty_directory(tmp_path):
    folder_name = "empty_folder"
    empty_folder = EmptyFolder(name=folder_name)
    zip_fly = ZipFly([empty_folder])

    zip_path = tmp_path / "empty_folder.zip"
    with zip_path.open("wb") as fp:
        for chunk in zip_fly.stream():
            fp.write(chunk)

    # Ensure folder_name ends with '/'
    if not folder_name.endswith('/'):
        folder_name += '/'

    with zipfile.ZipFile(zip_path) as zfp:
        # Check that the folder entry is present in the zip
        assert folder_name in zfp.namelist()

        # Extract the ZipInfo for the folder and check if it is marked as a directory
        info = zfp.getinfo(folder_name)
        assert info.is_dir()  # True means it's a directory entry

        # Reading the folder entry should yield empty content
        with zfp.open(folder_name) as folder_file:
            content = folder_file.read()
            assert content == b""

def _read_local_flags(data, offset):
    return struct.unpack_from("<H", data, offset + 6)[0]


def _read_central_flags(data, offset):
    return struct.unpack_from("<H", data, offset + 8)[0]


def test_non_ascii_file_names_utf8_flag(tmp_path):
    file_path = tmp_path / "input.bin"
    file_path.write_bytes(lorem_ipsum)

    files = [
        LocalFile(file_path=file_path, name="zażółć.txt"),
        LocalFile(file_path=file_path, name="файл.txt"),
        LocalFile(file_path=file_path, name="αρχείο.txt"),
        LocalFile(file_path=file_path, name="ファイル.txt"),
        LocalFile(file_path=file_path, name="文件.txt"),
    ]

    zip_path = tmp_path / "non_ascii_flags.zip"
    zipfly = ZipFly(files)

    with open(zip_path, "wb") as f:
        for chunk in zipfly.stream():
            f.write(chunk)

    data = zip_path.read_bytes()

    UTF8_FLAG = 0x0800

    # --- scan local headers ---
    offset = 0
    while True:
        sig = data.find(b"PK\x03\x04", offset)
        if sig == -1:
            break

        flags = _read_local_flags(data, sig)
        assert flags & UTF8_FLAG, f"UTF-8 flag missing in local header at {sig}"

        offset = sig + 4

    # --- scan central directory ---
    offset = 0
    while True:
        sig = data.find(b"PK\x01\x02", offset)
        if sig == -1:
            break

        flags = _read_central_flags(data, sig)
        assert flags & UTF8_FLAG, f"UTF-8 flag missing in central dir at {sig}"

        offset = sig + 4


DATA_DESCRIPTOR_FLAG = 0x0008

def _parse_local_file_header(data: bytes, offset: int = 0):
    signature = struct.unpack_from("<I", data, offset)[0]
    assert signature == 0x04034B50

    flags = struct.unpack_from("<H", data, offset + 6)[0]
    filename_len, extra_len = struct.unpack_from("<HH", data, offset + 26)

    filename_start = offset + 30
    filename_end = filename_start + filename_len

    extra_start = filename_end
    extra_end = extra_start + extra_len

    return {
        "flags": flags,
        "filename": data[filename_start:filename_end],
        "extra_len": extra_len,
        "extra": data[extra_start:extra_end],
        "filename_start": filename_start,
        "filename_end": filename_end,
        "extra_start": extra_start,
        "extra_end": extra_end,
        "file_data_start": extra_end,
    }


def test_extra_field_exists_after_local_file_header_and_no_data_descriptor(tmp_path):
    name = "gen_known_size_file.txt"

    file = GenFile(
        name=name,
        generator=lorem_ipsum_generator(),
        size=len(lorem_ipsum),
        crc=zlib.crc32(lorem_ipsum),
    )

    zip_path = tmp_path / f"genFile_extra_field.zip"
    zipfly = ZipFly([file])

    with zip_path.open("wb") as fp:
        for chunk in zipfly.stream():
            fp.write(chunk)

    data = zip_path.read_bytes()
    header = _parse_local_file_header(data)

    encoded_name = name.encode()

    assert header["filename"] == encoded_name

    assert header["filename_start"] == 30
    assert header["filename_end"] == 30 + len(encoded_name)
    assert header["extra_start"] == header["filename_end"]

    assert header["extra_len"] > 0
    assert len(header["extra"]) == header["extra_len"]

    assert header["file_data_start"] == header["extra_end"]
