"""
baudrate typically it is 9600, 19200, 115200

UTF-8 encoding used

"""

from machine import UART

if __name__ == '__main__':
    message = "1,2,3,4,5"

    uart = UART(0, baudrate=19200, bits=8, parity=0, stop=1)
    uart.write(message + "\n")

