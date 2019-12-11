import os

path = 'New text file'
op = os.path

print("Path: " + path)
print("File path: " + op.abspath(path))
print("File directory path: " + op.dirname(path))
print("File name + file type: " + op.basename(path))
