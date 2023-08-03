import array
import time
import struct

import serial


def single(s, pin: int, mode: int) -> int:
    s.write(f"s{pin:02}{mode}\n".encode())
    reply = s.read(2)
    value = struct.unpack("h", reply)[0]
    return value


def time_single(s):
    n = 1000
    start = time.perf_counter()
    for i in range(n):
        single(s, 0, 0)
    end = time.perf_counter()
    print(end-start, n/(end-start))


def continuous(s):
    n = 100000

    s.write(f"c{0:02}{0}{1:02}{0}\n".encode())
    time.sleep(1)
    for i in range(n):
        if s.in_waiting > 16:
            s.flushInput()
        reply = s.readline().decode() #.strip()
        print(reply)
        if i == 10:
            s.write(f"stop\n\r".encode())
    s.flushInput()
    print("hi")


def set_offset_gain(s):
    n = 10
    for i in range()

def main():
    s = serial.Serial(port="COM3")
    s.flushOutput()
    s.flushInput()

    try:

        continuous(s)

    finally:
        s.close()


if __name__ == "__main__":
    main()
