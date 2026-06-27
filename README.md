# ZipFly

<a href="http://forthebadge.com/"><img src="https://forthebadge.com/images/badges/0-percent-optimized.svg" alt="forthebadge"/></a>
<a href="http://forthebadge.com/"><img src="https://forthebadge.com/images/badges/gluten-free.png" alt="forthebadge"/></a>
<a href="http://forthebadge.com/"><img src="https://web.archive.org/web/20230604002050/https://forthebadge.com/images/badges/mom-made-pizza-rolls.svg" alt="forthebadge"/></a>

<img src="https://img.shields.io/badge/ZIP64-Certified-lightGreen" alt="Build Status"/>
<img src="https://img.shields.io/badge/build-failing-red" alt="Build Status"/>
<img src="https://img.shields.io/badge/made with-hate-orange" alt="Build Status"/>
<img src="https://img.shields.io/badge/fuck-zip-green" alt="Build Status"/>


**Python library to construct a ZIP64 archive on the fly 
without having to store the entire ZIP in 
memory or disk. This is useful in memory-constrained environments, or when you would like to start 
returning compressed data before you've even retrieved all the uncompressed data. 
Generating ZIPs on-demand in a web server is a typical use case for zipFly.**


- No temporary files, data is streamed directly
- Support for **async** interface 
- Calculates archive size before streaming even begins
- Supports `deflate` compression method
- Small memory usage, streaming is done using yield statement
- Archive structure is created on the fly, and all data can be created during stream
- Files included into archive can be generated on the fly using Python generators
- **Independent of the goofy 🤮🤮 python's standard ZipFile implementation**
- Only 1 dependency
- Automatic detection and changing of duplicate names
- `Zip64` format compatible files
- **21.37%** test coverage


This library is based upon [this library](https://github.com/kbbdy/zipstream) <sub>_(this library was a piece of work...)_<sub>

## How to install
    pip install zipfly64

https://pypi.org/project/zipFly64

## Usage

```py
from zipFly import ZipFly, LocalFile, consts
# compression_method is optional, defaults to consts.NO_COMPRESSION
file1 = LocalFile(file_path='files/lqbfa61deebf1.mp4', compression_method=consts.NO_COMPRESSION) #  or consts.COMPRESSION_DEFLATE 
file2 = LocalFile(file_path='public/2ae9dcd01a3aa.mp4', name="files/my_file2.mp4")  # override the file name
file3 = LocalFile(file_path='files/4shaw1dax4da.mp4', name="my_file3.mp4")  # you control the directory path by specifying it in name

files = [file1, file2, file3]

zipFly = ZipFly(files)

# save to file, or do something else with the stream() generator
with open("out/file.zip", 'wb') as f_out:
    for chunk in zipFly.stream():
        f_out.write(chunk)
```


### Supports dynamically created files
```py
from zipFly import ZipFly, GenFile, LocalFile, consts


def file_generator():
    yield b"uga buga"
    yield b"a29jaGFtIGFsdGVybmF0eXdraQ=="
    yield b"2137"
    
# size is optional, it allows to calculate the total size of the archive before any data is generated
# modification_time in epoch time, defaults to time.time()
file1 = GenFile(name="file.txt", generator=file_generator(), modification_time=time.time(), size=size, compression_method=consts.COMPRESSION_DEFLATE)
file2 = LocalFile(file_path='files/as61aade2ebfd.mp4', compression_method=consts.NO_COMPRESSION) #  or consts.COMPRESSION_DEFLATE 

files = [file1, file2]

zipFly = ZipFly(files)
archive_size = zipFly.calculate_archive_size() # raises RuntimeError if it can't calculate size

# for example you can set as content length in http response
response['Content-Length'] = archive_size

for chunk in zipFly.stream():
       # do something
```

> [!TIP]
> Files can also be created lazily. Byte offset will still work. `calculate_archive_size()` will not.

## Async interface

```py
import asyncio
from zipFly import ZipFly, LocalFile, consts, GenFile
file1 = GenFile(name="file.txt", generator=file_generator())
file2 = LocalFile(file_path='public/2ae9dcd01a3aa.mp4', name="files/my_file2.mp4")

files = [file1, file2]

zipFly = ZipFly(files)

async def save_zip_async():
    with open("out/file.zip", 'wb') as f_out:
        async for chunk in zipFly.async_stream():
            f_out.write(chunk)

asyncio.run(save_zip_async())
```
> [!NOTE]  
> file_generator must be async. Local file async streaming is done with aiofiles library.


## Byte offset mode
> [!TIP]
> Use this with Byte Range header to allow for resumable zip streaming

This mode allows to start generating archive from offset. It finds the file within that offset and starts streaming 
from it. Sadly it must fetch the entire file as otherwise a correct crc cannot be calculated.
If you use `LocalFile` then it's not a problem as it can very fast go tru the entire local file 
and calculate crc. However, if u use a `GenFile` it still has to fetch the entire file which may take a while 
depending on the file's size.

```py

file1 = GenFile(name="file.txt", generator=file_generator(), crc=crc)
file2 = LocalFile(file_path='public/2ae9dcd01a3aa.mp4', name="files/my_file2.mp4")
files1 = [file1, file2]
zipFly1 = ZipFly(files1)

# Simulating pause/resume
STOP_BYTE = 300
async def async_save_pause():
    byte_offset = 0
    with open("out/file.zip", 'wb') as f_out:
        async for chunk in zipFly1.async_stream():
            remaining_bytes = STOP_BYTE - byte_offset
            if len(chunk) > remaining_bytes:
                chunk = chunk[:remaining_bytes]
            f_out.write(chunk)
            byte_offset += len(chunk)
            if byte_offset >= STOP_BYTE:
                break
                
# Later...                
file3 = GenFile(name="file.txt", generator=file_generator(), crc=crc)
file4 = LocalFile(file_path='public/2ae9dcd01a3aa.mp4', name="files/my_file2.mp4")
files2 = [file3, file4]
resumeZipFly = ZipFly(files2, byte_offset=STOP_BYTE)

async def async_save_resume():
    with open("out/file.zip", 'ab') as f_out: # Append mode
        async for chunk in resumeZipFly.async_stream():
            f_out.write(chunk)

async def pause_resume_save():
    await async_save_pause()
    await async_save_resume()

asyncio.run(pause_resume_save())
```
If resume ZipFly instance has different files than pause ZipFly instance there will be a corrupted Zip file generated

> [!NOTE]  
> For byte offset mode to work you must use `const.NO_COMPRESSION` and specify `crc` for `GenFile`

> [!CAUTION]
> You mustn't reuse `ZipFly` instances. They should be re-created everytime you call `stream()` or `async_stream()`

> [!CAUTION]
> You mustn't reuse `File` instances. 


## Parallel async streaming

If your `GenFile`'s rely on network requests to fetch data, network latency can limit throughput
below the available bandwidth. To address this, I introduce `async_stream_parallel`.

```python
zipFly = ZipFly(files)
zipFly.async_stream_parallel(prefetch_files=20, max_chunks_per_file=2)
```

### Other
Python is not optimized for async I/O operations, thus to speed up the async streaming the chunk_size is changed to 4MB, you can override this by passing `chunksize` as argument to LocalFile.

I created this library for my [iDrive](https://github.com/pam-param-pam/I-Drive) project.

If you have a different use case scenario, and LocalFile and GenFile are not enough, you can extend BaseFile and everything else should work out of the box.

I found myself needing to write custom payloads after `local file headers` and before the actual file data. You can pass `custom_payload` to `File` instances.
### Testing

With [pytest](https://docs.pytest.org/en/stable/) and
[pytest-asyncio](https://pytest-asyncio.readthedocs.io/en/stable/) installed,
call `pytest` from the top-level directory (same as this `README.md`)
to run tests.
The 4GB tests are slow. If your machine has enough memory (~4GB free) and a fast
disk/SSD, [pytest-xdist](https://pytest-xdist.readthedocs.io/en/stable/)
can speed things up by running tests in parallel.
Use it by calling `pytest -n auto`.

### PS

I wholeheartedly hope everyone responsible for creating ZIP documentation gets slaughtered in the most gore and painful way 😊 (in game)

(pls redo ur [docs](https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT))


