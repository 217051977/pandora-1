f = open("go.sh", 'w+')
for i in range(1,70):
	f.write("../../code/muda < test" +str(i) + ".in > test" + str(i) + ".out\n")
f.write("find -iname \"*.in\" -o \".out\" | xargs zip testes.zip")
f.close
