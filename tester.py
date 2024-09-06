from zipFly import ZipFly, LocalFile

file1 = LocalFile(file_path='files/lqbfa61deebf12ae9dcd01a3aaa70627c1.mp4')
file2 = LocalFile(file_path='files/test1.mp4')
file3 = LocalFile(file_path='files/The_Little_Mermaid.mp4')
file4 = LocalFile(file_path='files/test1.mp4')
file5 = LocalFile(file_path='files/test1.mp4')
file6 = LocalFile(file_path='files/test1.mp4')

files = [file1, file2, file4, file5, file6] #, file4, file5, file6



zip_stream = ZipFly(files)

with open("out/file.zip", 'wb') as f_out:
    for chunk in zip_stream.stream():
        f_out.write(chunk)
