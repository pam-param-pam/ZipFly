
from zipstream.LocalFile import LocalFile
from zipstream.ZipBase import ZipFly


file1 = LocalFile(file_path='files/lqbfa61deebf12ae9dcd01a3aaa70627c1.mp4')
file2 = LocalFile(file_path='files/test1.mp4')

files = [file1, file2]
zip_stream = ZipFly(files)

print(zip_stream.calculate_archive_size())
with open("out/file.zip", 'wb') as f_out:
    for chunk in zip_stream.stream():
        f_out.write(chunk)
