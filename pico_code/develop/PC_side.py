
import serial
import time


def main():
    s = serial.Serial(port="COM3", parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE, timeout=1)
    s.flushOutput()
    s.flushInput()

    s.write("v\n".encode())
    mes = s.read_until()
    print(mes.decode().strip("\n"))


if __name__ == "__main__":
    main()
