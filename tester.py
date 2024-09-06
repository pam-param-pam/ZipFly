# from zipstream import ZipStream
#
from zipstream.ZipBase import ZipFly

# file2_obj = open("files/lqbfa61deebf12ae9dcd01a3aaa70627c1.mp4", 'rb')
# file3_obj = open("files/The Little Mermaid.mp4", 'rb')
#
#
# # Function to create a generator that reads a file in chunks
def file_generator(file_obj, chunk_size=1024):
    """Generator function to read a file in chunks."""
    while True:
        chunk = file_obj.read(chunk_size)
        if not chunk:
            break
        yield chunk
#
#
# files = []
# print(file1_obj.name)
# file1_dict = {'name': file1_obj.name,
#               'stream': file_generator(file1_obj),
#               "size": file1_obj.__sizeof__(),
#               "cmethod": None
#               }
#
# file2_dict = {'name': file2_obj.name,
#               'stream': file_generator(file2_obj),
#               "size": file2_obj.__sizeof__(),
#               "cmethod": None
#               }
#
# file3_dict = {'name': file3_obj.name,
#               'stream': file_generator(file3_obj),
#               "size": file3_obj.__sizeof__(),
#               "cmethod": None
#               }
#
# files.append(file1_dict)
# files.append(file2_dict)
# files.append(file3_dict)
#
# zip_stream = ZipStream(files)
#
# with open("out/file.zip", 'wb') as f_out:
#     for chunk in zip_stream.stream():
#         f_out.write(chunk)
#
from zipstream.GenFile import GenFile

file1_obj = open("files/lqbfa61deebf12ae9dcd01a3aaa70627c1.mp4", 'rb')
file2_obj = open("files/test1.mp4", 'rb')

file1 = GenFile(name_path='files/lqbfa61deebf12ae9dcd01a3aaa70627c1.mp4', generator=file_generator(file1_obj), size=file1_obj.__sizeof__())
file2 = GenFile(name_path='files/test1.mp4', generator=file_generator(file2_obj), size=file2_obj.__sizeof__())

files = [file1, file2]
zip_stream = ZipFly(files)

with open("out/file.zip", 'wb') as f_out:
    for chunk in zip_stream.stream():
        f_out.write(chunk)