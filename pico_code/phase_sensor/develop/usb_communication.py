from machine import UART, Pin
from utime import sleep
import sys
import select


def main():
    led = Pin(25, Pin.OUT)
    led.value(1)

    try:
        file = open('usb_testing.txt', 'a')
        file.write("trying")
        k = 0
        while True:
            while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                ch = sys.stdin.read(1)
                file.write(str(ch) + str(type(ch)))
                led.toggle()
                if ch == "r":
                    k = k + 1
                    print("ddddddddddd" + str(k))
                    # sys.stdin.write(b"d\n")
                # sleep(0.01)

    finally:
        led.value(0)
        file.close()


