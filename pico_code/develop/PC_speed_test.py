
import serial
import time

s = serial.Serial(port="COM3", baudrate=110, parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE)
s.flushOutput()
s.flushInput()


def main():
    n = 3000
    s.write("single\r".encode())
    mes = s.read_until()
    # offset = int(mes.decode().strip("\n").strip("\r")) + 1

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
        result = mes.decode().strip("\n").strip("\r")
        if f"a 1" != result:
            print(f"{i} 1", f" return:{result}")
            raise ValueError()

    end = time.perf_counter()
    print(end-start, " ", n/(end-start))
    print("read: ", time_read)
    print("write: ", time_write)


def main2():
    s = serial.Serial(port="COM3", parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE, timeout=1)
    s.flush()

    n = 100000

    s.write("single\r".encode())
    mes = s.read_until()
    print(mes.decode())

    s.write(f"burst{n}\r".encode())
    start = time.perf_counter()
    data = []
    for i in range(n+3):
        # print(i)
        mes = s.read_until().decode().strip("\n")
        data.append(mes)
        if mes == "end\r":
            print(f"end: {i}")
            break

    end = time.perf_counter()
    print(end-start, " ", n/(end-start))
    # print(data)


if __name__ == "__main__":
    main()

