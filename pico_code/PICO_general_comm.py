"""
General Communication Code:

This code is used on multi-purpose Picos.
It takes commands over USB and based on the message it receives it can run various different functions.


Wiring:
    **PC**                  **Pico**
    usb                     usb

"""

import sys
import select

# Available functions
from valve import servo


def main():
    file = open('usb_testing.txt', 'a')
    file.write("trying")

    # main loop (infinite loop)
    while True:
        while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            # read how long the message will be
            message_length = sys.stdin.read(1)
            try:
                message_length = int(message_length)
                message2 = sys.stdin.read(message_length)
            except ValueError:
                continue

            ### Do stuff ###
            # Reply to poll
            if message2[0] == "a":
                options = ["a", "v", "t", "r", "l"]
                print("a" + "general_pico;" + str(options))
                continue

            # Valve
            if message2[0] == "v":
                pin = int(message2[1:3])
                duty = int(message2[4:8])
                servo(pin=pin, duty=duty)
                print("v")

            # Analog reading
            if message2[0] == "t":
                print("t")

            # On/Off Relay
            if message2[0] == "r":
                print("r")

            # LED dim
            if message2[0] == "l":
                print("l")



