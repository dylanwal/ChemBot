"""
Valve Class

"""

import warnings
import logging
from time import time

from serial import Serial, PARITY_EVEN, STOPBITS_ONE
import numpy as np

import os

from main_code.core_equip import Valve
from main_code.core_equip import communication
from main_code.utils.pico_checks import check_GPIO_pins

# file_loc = os.path.join(os.path.dirname(__file__), 'data/')


class ValveServo(Valve):
    def __init__(self, servo_timing: list[int], pin: int, comm_port: str, **kwargs):
        """

        :param servo_timing:
        :param pin:
        :param comm_port: COM port; format COM#
        :param args:
        :param kwargs:
        """
        super().__init__(**kwargs)

        # Will be all set in _servo_check
        self.pin = None
        self.servo_timing = None
        self._servo_check(pin, servo_timing)

        self.serial = communication.connect_serial(comm_port=comm_port, **kwargs)

    def initialize(self, start_pos: int):
        """Needs to be defined in subclass."""
        self.state = "standby"
        self.move(start_pos)

    def execute(self, position):
        """Needs to be defined in subclass."""
        # Send command to pico
        _pin = str(self.pin).zfill(2)
        _pos = str(self.positions[position]).zfill(4)
        self.serial.write(f"v{_pin}{_pos}\r".encode())

        # reply from pico
        reply = self.serial.read_until()
        reply = reply.decode()
        if reply[0] == "v" and self.serial_comm.in_waiting == 0:
            return

        raise ConnectionError("no reply received. ")

    def _servo_check(self, pin, servo_timing):
        # Checking pin
        if type(pin) == int:
            if check_GPIO_pins(pin):
                self.pin = pin
            else:
                raise ValueError(f"pin out of valid range [0-28] (excluding 24). given {pin}")
        else:
            raise TypeError(f"pin invalid type; given: {type(pin)}, expect: int")

        # Checking servo timing
        for value in servo_timing:
            if type(value) != int:
                raise TypeError(f"invalid type in servo_timing. given: {type(value)}, expected: int")
            if 400 > value > 2600:
                raise ValueError(f"servo_timing outside expected range [400, 2600]. given: {value}")
        self.servo_timing = servo_timing


if __name__ == '__main__':
    """
    Example code for a single valve.
    You will likely need to change the COM port to match your devices.
    Cycles through positions once.

    Output: Prints to screen the position. 
    """
    # from time import sleep
    #
    # # Logging stuff
    # logging.basicConfig(filename=r'.\testing.log',
    #                     level=logging.DEBUG,
    #                     format='%(asctime)s %(message)s',
    #                     datefmt='%m/%d/%Y %I:%M:%S %p')
    # logging.info("\n\n")
    # logging.info("---------------------------------------------------")
    # logging.info("---------------------------------------------------")



    # Initiate to servo valve
    V1 = ValveServo(servo_timing=servo_timing, pin=15)

    print("Done")
