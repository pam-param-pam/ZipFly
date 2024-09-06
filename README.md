# ZipFly

ZipFly is a library for creating & streaming zip64 archives "on the fly".

It allows to create/fetch file content dynamically while the archive is streamed.

- No temporary files, data is streamed directly
- Supported `deflate` compression method
- Small memory usage, streaming is done using yield statement
- Archive structure is created on the fly, and all data can be created during stream
- Files included into archive can be generated on the fly using Python generators
- **Independent of the goofy 🤮🤮 python's standard ZipFile implementation**
- No dependencies
- `Zip64` format compatible files


This library is based upon [this library](https://twitter.com/) <sub>_(this library was a piece of work...)_<sub>

## Typical Usage

```py
from zipFly import ZipFly, LocalFile, consts
# compression_method is optional, defaults to consts.NO_COMPRESSION
file1 = LocalFile(file_path='files/lqbfa61deebf1.mp4', compression_method=consts.NO_COMPRESSION) #  or consts.COMPRESSION_DEFLATE 
file2 = LocalFile(file_path='public/2ae9dcd01a3aa.mp4', name="files/my_file2.mp4")  # override the file name
file3 = LocalFile(file_path='files/4shaw1dax4da.mp4', name="my_file3.mp4")  # You control the directory path by specifying it in name

files = [file1, file2, file3]

zip_stream = ZipFly(files)

# save to file, or do something else with the stream() generator
with open("out/file.zip", 'wb') as f_out:
    for chunk in zip_stream.stream():
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

zip_stream = ZipFly(files)
archive_size = zip_stream.calculate_archive_size()

# for example you can set as content length in http response
response['Content-Length'] = archive_size

for chunk in zip_stream.stream():
       # do something

```

### PS

I wholeheartedly hope everyone responsible for creating ZIP documentation gets slaughtered in the most gore and painful way 😊 

(pls redo ur [docs](https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT))


