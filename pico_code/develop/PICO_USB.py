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

