
import serial
import time


def main():
    s = serial.Serial(port="COM4", baudrate=115200, parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE)
    s.flush()

    n = 10000

    s.write("a\r".encode())
    mes = s.read_until()
    offset = int(mes.decode().strip("\n").strip("\r")) + 1

    start = time.perf_counter()
    time_write = 0
    time_read = 0
    for i in range(n):
        write_start = time.perf_counter()
        s.write("a\r".encode())
        time_write += time.perf_counter() - write_start
        read_start = time.perf_counter()
        mes = s.read_until()
        time_read += time.perf_counter() - read_start
        result = int(mes.decode().strip("\n").strip("\r"))
        if i + offset != result:
            print(f"i:{i+ offset}", f" return:{result}")
            raise ValueError()

    end = time.perf_counter()
    print(end-start, " ", n/(end-start))
    print("read: ", time_read)
    print("write: ", time_write)


if __name__ == "__main__":
    main()

"""


import select
import sys
import machine


def main():
    initialization()
    main_loop()


def initialization():
    # set all pins to low right away
    for i in range(28):
        machine.Pin(i, machine.Pin.OUT).value(0)

    # Turn LED on
    machine.Pin(25, machine.Pin.OUT).value(1)


def main_loop():
    # main loop (infinite loop)
    i = 0
    while True:
        while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            # read in message (till it sees '\r')
            message = sys.stdin.readline()

            ### Do stuff ###
            # Reply to poll
            if message[0] == "a":
                print(i)
                i += 1
            
    
if __name__ == "__main__":
    main()

12.394042400002945   806.8392601269157
read:  11.278688497724943
write:  1.0693300979910418
"""