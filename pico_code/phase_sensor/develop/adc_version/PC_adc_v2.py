import time
import numpy as np

import serial


def format_pin(pin: int, mode: int) -> str:
    return f"{pin:02}{mode}"


def single(s, pins: list[int], modes: list[int]) -> np.array:
    s.write(("s" + "".join(format_pin(pin, mode) for pin, mode in zip(pins, modes)) + "\n").encode())
    reply = s.readline().decode().strip().split(",")
    return np.array(reply, dtype=np.uint16)


def continuous(s, n: int = 200):
    s.write(f"c{0:02}{0}{1:02}{0}\n".encode())
    for i in range(n):
        if s.in_waiting > 16:
            s.flushInput()
        reply = s.readline().decode().strip().split(",")
        data = np.array(reply, dtype=np.uint16)
        # print(data)

    s.write(f"stop\n\r".encode())
    s.flushInput()


def set_gain(s, value: int):
    """ 1,2,4,8,16"""
    # write PGA gain
    s.write(f"g{8:02}\n".encode())
    reply = s.readline().decode().strip()
    if reply[0] != "g":
        raise ValueError(f"unexpected reply from pico. received: {reply}")


def set_offset_gain(s):
    set_gain(s, 1)
    n = 10
    data = np.zeros(2, dtype=np.uint16)
    for i in range(n):
        data += single(s, [0, 1], [0, 0])

    # 16 bit resolution adc = 2**16 -1   (minus 1 is it starts at zero)
    # divide by 2 as the 16 bit is center at zero with both positive and negative
    # 5 volts is used
    voltage = np.mean(data) / ((2**16 - 1)/2) * 5

    # write DAC voltage
    s.write(f"o{voltage:.06}\n".encode())
    reply = s.readline().decode().strip()
    if reply[0] != "o":
        raise ValueError(f"unexpected reply from pico: {reply}")

    set_gain(s, 4)


def time_single(s):
    n = 1000
    start = time.perf_counter()
    for i in range(n):
        single(s, [0, 2], [1, 1])
    end = time.perf_counter()
    print("single", end-start, n/(end-start))


def time_continuous(s):
    n = 1000
    start = time.perf_counter()
    continuous(s, n)
    end = time.perf_counter()
    print("continuous:", end-start, n/(end-start))


def main():
    s = serial.Serial(port="COM3")
    s.flushOutput()
    s.flushInput()

    try:
        # set_offset_gain(s)
        # continuous(s)
        time_single(s)
        time_continuous(s)

    finally:
        s.close()


if __name__ == "__main__":
    main()
