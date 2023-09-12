
import serial
import time


def main():
    s = serial.Serial(port="COM3")
    s.flushOutput()
    s.flushInput()

    s.write("v\n".encode())
    mes = s.read_until()
    print(mes.decode().strip("\n"))


if __name__ == "__main__":
    main()
