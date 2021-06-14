"""
This code is for the Harvard Apparatus PHD 2000 syringe pumps.
Pumps receive RS-232 serial commands.

"""

from machine import UART, Pin
from utime import ticks_ms, sleep
import ubinascii


def timeout_read(_uart, timeout_ms=20):
    now = ticks_ms()
    value = b''
    while True:
        if (ticks_ms() - now) > timeout_ms:
            break
        if _uart.any():
            value = value + _uart.read(1)
            now = ticks_ms()
    return value


def polling(_uart):
    """
    This function is to determine what controls we have acess to.
    para: _uart: uart object
    return: active: list with active pump ids
    """
    active = []
    for i in range(2):  # looping over pumps
        responce = 0
        for ii in range(3):  # giving each pump 3 attempts to reply
            message = str(i + 1) + "R"  # destination + acknowledgement
            message = add_checksum(message)
            message = message + '\r'

            if i == 0:  # A [CR] must start the network.
                message = '\r' + message

            # ping pump
            message = '\r1R5D\r'
            print(message)
            _uart.write(message)

            # wait for reply
            responce = timeout_read(_uart, timeout_ms=20)
            print(responce)

            if responce:
                active.append(i + 1)
                break
            sleep(0.1)

    return active


def main():
    uart = UART(0, 9600, bits=8, parity=None, stop=2)
    led = Pin(25, Pin.OUT)
    led.toggle()

    address = 1
    message = '{0:02.0f}'.format(address) + 'VER' + '\r'
    # message = '{0:02.0f}'.format(address) + 'RUN' + '\r'
    # message = '{0:02.0f}'.format(address) + 'ULM' + '1' + '\r'
    print("sent message: " + str(message))
    uart.write(message)
    responce = timeout_read(uart, timeout_ms=200)
    print("recieved message: " + str(responce))

    led.toggle()


if __name__ == "__main__":
    main()
