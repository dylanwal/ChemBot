import time
import numpy as np

import serial


def format_pin(pin: int, mode: int) -> str:
    return f"{pin:02}{mode}"


def single(s, pins: list[int], modes: list[int]) -> np.array:
    s.write(("s" + "".join(format_pin(pin, mode) for pin, mode in zip(pins, modes)) + "\n").encode())
    reply = s.readline().decode().strip().split(",")
    return np.array(reply, dtype=np.int16)


def leds_power(s, value: int = 0):
    s.write(f"d{value}\n".encode())
    time.sleep(0.1)
    reply = s.readline().decode().strip()
    if reply[0] != "d":
        raise ValueError(f"unexpected reply from pico. received: {reply}")


def set_gain(s, value: int = 1):
    """ 1,2,4,8,16"""
    # write PGA gain
    s.write(f"g{value:02}\n".encode())
    reply = s.readline().decode().strip()
    if reply[0] != "g":
        raise ValueError(f"unexpected reply from pico. received: {reply}")

gains = {
    1: 4.096,
    2: 2.048,
    4: 1.024,
    8: 0.512,
    16: 0.256
}


def set_offset_gain(s, gain: int=16):
    set_gain(s, 1)
    n = 10
    leds_power(s, 0)
    data = np.zeros((n, 2), dtype=np.int16)
    for i in range(n):
        data[i, :] = single(s, [0, 1], [0, 0])

    # 16 bit resolution adc = 2**16 -1   (minus 1 is it starts at zero)
    # divide by 2 as the 16 bit is center at zero with both positive and negative
    # 5 volts is used
    voltage = np.mean(np.mean(data, axis=0)) / ((2**16 - 1)/2) * 4.096
    print(voltage)
    voltage += gains[gain]/1.5

    # write DAC voltage
    s.write(f"o{voltage:.06}\n".encode())
    reply = s.readline().decode().strip()
    if reply[0] != "o":
        raise ValueError(f"unexpected reply from pico: {reply}")

    set_gain(s, gain)
    leds_power(s, 1)


def time_single(s):
    n = 1000
    leds_power(s, 0)
    start = time.perf_counter()
    for i in range(n):
        single(s, [0, 1], [1, 1])
    end = time.perf_counter()
    leds_power(s, 1)
    print("single", end-start, n/(end-start))


def print_single(s):
    n = 100
    leds_power(s, 0)
    time.sleep(0.2)
    for i in range(n):
        data = single(s, [0, 1], [1, 1])
        print(data)
    leds_power(s, 1)


def main():
    s = serial.Serial(port="COM3")
    s.flushOutput()
    s.flushInput()

    try:
        set_offset_gain(s)
        print_single(s)
        # time_single(s)

    finally:
        s.close()


if __name__ == "__main__":
    main()
