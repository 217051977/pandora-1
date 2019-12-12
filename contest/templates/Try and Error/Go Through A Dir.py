import os

path = '/home/bruno/dev/pandora_V2/contest/templates/Try and Error/Files/1234.zip'

print("\nFile path: " + path)

count = 0

for c in os.walk(os.path.dirname(path)):
    count += 1

pos = 0

print("start")

for file in os.walk(os.path.dirname(path)):
    print(file)
    pos += 1
    if pos == count:
        print(str(file[len(file) - 1]) + "\n\n")
        for f in file[len(file) - 1]:
            print(f)
            f_parts = f.split('.')
            print(f_parts[len(f_parts) - 1])
