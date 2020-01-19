import time

_count = 0
_delay = 120

while(1):
    with open("SWITCH_VNF", "r+") as f:  
        _count += 1
        print(_count)

        data = f.read().rstrip()
        print(data)
        if data == "CON":
            f.seek(0)
            f.write("VM")
            f.truncate()
            _delay = 100
        if data == "VM":
            f.seek(0)
            f.write("CON")
            f.truncate()
            _delay = 20

    if _count > 45:
        break
    time.sleep(_delay)


# # f = open("demofile2.txt", "a")
# f.write("Now the file has more content!")
# f.close()
