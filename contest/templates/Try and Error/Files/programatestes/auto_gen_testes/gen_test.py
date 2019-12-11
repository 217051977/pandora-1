import random

def numberGenerator(base):
	set = ['0', '1', '2','3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
	set = set[0:base]
	number = list()
	limit = random.randint(1,10-base/4)
	randnum = ''
	for x in range(0,limit):
		randnum = random.choice(set)
		while(x == 0 and randnum == '0'):
			randnum = random.choice(set)
		number.append(random.choice(set))
	return ''.join(number)

#Number of files
for base in range(2, 36):
	print("File: test" + str(36+base-1) + ".in")
	f = open("test" + str(36+base-1)+ ".in", 'w+')
	for destination in range(2, 36):
		if(destination != base):
			number = numberGenerator(destination)
			f.write("c " + number + " " + str(destination) + " " + str(base) + "\n")
	f.write("q\n")
	f.close()
print("Finished!")
