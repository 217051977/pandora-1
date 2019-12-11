from os import walk, remove
from os.path import dirname

path = '/home/bruno/dev/pandora_V2/contest/templates/Try and Error/Files/dev/pandora_V2/contest/templates/Try and Error'

print("\nFile path: " + path)

count = 0

for c in walk(dirname(path)):
    count += 1

pos = 0

print("start")

for file in walk(dirname(path)):
    print(file)
    pos += 1
    if pos == count:
        print(str(file[len(file) - 1]) + "\n\n")
        for f in file[len(file) - 1]:
            print(f)
            remove(str(file[0]) + "/" + str(f))
