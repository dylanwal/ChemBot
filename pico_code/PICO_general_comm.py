"""
General Communication Code:

This code is used on multi-purpose Picos.
It takes commands over USB and based on the message it receives it can run various different functions.


Wiring:
    **PC**                  **Pico**
    usb                     usb

"""

import select
import sys
import machine

# Available functions
from valve import servo


def main():
    # set all pins to low right away
    for i in range(28):
        machine.Pin(i, machine.Pin.OUT).value(0)

    # Turn LED on
    machine.Pin(25, machine.Pin.OUT).value(1)

    # main loop (infinite loop)
    while True:
        while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            # read in message (till it sees '\r')
            message = sys.stdin.readline()

            ### Do stuff ###
            error = ""
            # Reply to poll
            if message[0] == "a":
                options = ["a", "v", "t", "r", "l"]
                print("a" + "general_pico;" + str(options))
                continue

            # Valve
            if message[0] == "v":
                try:
                    _pin = int(message[1:3])  # GPIO pins: 0 - 28
                    duty = int(message[4:8])  # in milli-seconds or micro-seconds
                    servo(_pin=_pin, duty=duty)
                    print("v")
                    continue
                except Exception as e:
                    error = str(type(e)) + " " + str(e)

            # Analog reading
            if message[0] == "t":
                try:
                    _pin = int(message[1:3])  # GPIO pins: 26, 27, 28 or ADC - 0, 1, 2, 3(internal Vsys), 4(internal temp.)
                    reading = machine.ADC(_pin).read_u16()
                    print("t" + str(reading))
                    continue
                except Exception as e:
                    error = str(type(e)) + " " + str(e)

            # On/Off Relay
            if message[0] == "r":
                try:
                    _pin = int(message[1:3])  # GPIO pins: 0 - 28
                    _state = int(message[3])  # 0 or 1 only
                    machine.Pin(_pin, machine.Pin.OUT).value(_state)
                    print("r")
                    continue
                except Exception as e:
                    error = str(type(e)) + " " + str(e)

            # LED dim
            if message[0] == "l":
                try:
                    _pin = int(message[1:3])  # GPIO pins: 0 - 15 (over GPIO 15 are alternative GPIO pins for the same channels)
                    _freq = int(message[3:7])  # [8 - 9,999]
                    _duty = int(message[7:10])  # [0 - 100]
                    _pwm = machine.PWM(machine.Pin(_pin))
                    _pwm.freq(_freq)
                    _pwm.duty_u16(int(_duty / 100 * 65535))
                    print("l")
                    continue
                except Exception as e:
                    error = str(type(e)) + " " + str(e)

            # reset all
            if message[0] == "e":
                # set all pins to low
                for i in range(28):
                    machine.Pin(i, machine.Pin.OUT).value(0)
                # Turn LED on
                machine.Pin(25, machine.Pin.OUT).value(1)
                print("e")
                continue

            # invalid or error replies
            message = message.replace("\n", "")
            if error == "":
                print("Invalid message:" + str(message))
            else:
                print("Error in processing message (" + str(message) + "): " + error)

