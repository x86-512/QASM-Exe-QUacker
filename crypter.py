import sys
from random import randint

def main():
    key = randint(0,255)

    crypted_str = b""
    with open(sys.argv[1], 'rb') as exe:
        for i in exe.read()[:-1]: #Skip the added \n
            print(int(i))
            print((int(i)^key))
            print(bytes(int(i)^key))
            crypted_str+=(int(i)^key).to_bytes(1, 'little')
    print(crypted_str)
    with open(sys.argv[1], 'wb') as exe:
        exe.write(crypted_str)
    print("Successfully crypted the exe file")

if __name__=="__main__":
    main()
