import struct
import array
import time

import serial


def single_write_str(s):
    s.write('1,2,3,4,5\r'.encode())
    mes = s.read_all().decode()
    print(mes.replace("\n", "_n").replace("\r", "_r"))
    time.sleep(0.1)


def overall_test_str(s, n):
    start = time.perf_counter()
    for i in range(n):
        s.write('1,2,3,4,5\r'.encode())
        mes = s.read_all()

    end = time.perf_counter()
    print("total time", end-start, " sec | individual time", (end-start)/n, " sec | Hz: ", n/(end-start))


def single_write_array(s):
    arr = array.array("i", [1,2,3,4,5])
    s.write(b"0x01")
    # reply = s.read_until().decode()
    # print(reply)
    time.sleep(0.1)

def single_write_struct(s):
    arr = array.array("i", [1,2,3,4,5])
    s.write(arr.tobytes())
    reply = s.read_all()
    time.sleep(0.1)


def overall_test_byte_array(s, n):
    start = time.perf_counter()
    for i in range(n):
        arr = array.array("i", [1,2,3,4,5])
        s.write(arr.tobytes())
        mes = s.read_all()

    end = time.perf_counter()
    print("total time", end-start, " sec | individual time", (end-start)/n, " sec | Hz: ", n/(end-start))


def individual(s, n):
    start = time.perf_counter()
    time_write = 0
    time_read = 0
    for i in range(n):
        write_start = time.perf_counter()
        s.write("1\r".encode())
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


def main():
    s = serial.Serial(port="COM4")
    s.flushOutput()
    s.flushInput()

    n = 10_000

    # str
    # single_write(s)
    # overall_test_str(s, n)

    single_write_array(s)


if __name__ == "__main__":
    main()


"""
prompt: 1,2,3,4,5\n

1) string - print - no conversion to int  
    Hz:  1042.6089136330086
2) string - std - no conversion to int  
    Hz:  1100
3) string - std - int conversion - str(list)
    Hz:  431.58030348577034
3) string - std - int conversion - for loop list back to str
    Hz:  221.58030348577034
    
4) Rust
    Hz: 1100
"""

"""
"""
Communication speed test

"""
import time

import select
import sys
import machine
import array


def main():
    print("startup")
    reset()
    main_loop()


def reset():
    # set all pins to low right away
    for i in range(28):
        machine.Pin(i, machine.Pin.OUT).value(0)

    # Turn LED on
    machine.Pin(25, machine.Pin.OUT).value(1)


def write_to_file(message):
    file = open("text.txt","a")
    file.write(repr(type(message)))
    file.write(repr(message).replace("\n", "_n").replace("\r", "_r"))
    file.write('\n')
    file.close()


def string_input():
    message = sys.stdin.readline().strip()
    # write_to_file(message)
    sys.stdout.write(message + "\r")
    
    
def string_input_int():
    message = sys.stdin.readline().strip()
    # write_to_file(message)
    values = message.split(",")
    data = []
    for v in values:
        data.append(int(v))
        
    #text= ""
    #for d in data:
    #   text += str(d) + "," 
    #sys.stdout.write(text[:-1] +"\r")
    
    sys.stdout.write(str(data) +"\r")


def array_input():
    message = sys.stdin.read(1)
    write_to_file(message)
    sys.stdout.write(message)

def main_loop():
    # Set up the poll object
    poll_obj = select.poll()
    poll_obj.register(sys.stdin, select.POLLIN)

    while True:  # infinite loop
        poll_results = poll_obj.poll(10)
        if poll_results:
            try:
                string_input()
                # string_input_int()
                # array_input()
            except Exception as e:
                print(str(type(e)) + " " + str(e))
                write_to_file(str(type(e)) + " " + str(e))


if __name__ == "__main__":
    main()


"""