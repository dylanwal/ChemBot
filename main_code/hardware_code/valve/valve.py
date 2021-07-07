"""
Valve Class

"""

import warnings
import logging
from time import time

from serial import Serial, PARITY_EVEN, STOPBITS_ONE
import numpy as np

import os

file_loc = os.path.join(os.path.dirname(__file__), 'data/')


class Valve:
    instances = []

    def __init__(self,
                 name: str = None,
                 port: str = "COM6",
                 serial: Serial = None,
                 positions: list[list[str, int]] = None,
                 pin: int = 15
                 ):
        """

        :param name:
        :param port:
        :param serial:
        :param positions:
        :param pin: PW
        """

        if name is None:
            self.name = "valve_" + str(len(self.instance))
        else:
            self.name = name

        self.port = port
        # Setup communication
        if serial is None:
            self.serial_comm = Serial(port=port, baudrate=115200, parity=PARITY_EVEN, stopbits=STOPBITS_ONE,
                                      timeout=0.1)
        else:
            if isinstance(serial, Serial):
                self.serial_comm = serial
            else:
                raise ValueError(f"Phase sensor(name: {self.name}; port:{self.port}); Provide serial is not the right"
                                 f"type. (Use serial from Serial module.)")

        self.pin = pin
        self.position = None
        if positions is None:
            self.positions = [
                ["P1", 545],
                ["P2", 1190],
                ["P3", 1820],
                ["P4", 2480]
            ]
        else:
            for _key, _value in positions:
                if type(_key) != str:
                    raise TypeError(f"Valve ({self.name, self.port}): positions dictionary needs to have keys of type "
                                    f"strings and values of integers {_key}, {type(_key)}. (change type of 'key' to str)")
                if type(_value) != int:
                    raise TypeError(f"Valve ({self.name, self.port}): positions dictionary needs to have keys of type "
                                    f"strings and values of integers {_value}, {type(_value)}. (change type of 'value' to int)")
                if 400 < _value < 2600:
                    raise ValueError(
                        f"Valve ({self.name, self.port}): {_value} is outside the acceptable range for PWM "
                        f"timing.")
        self.pos_keys = [i[0] for i in self.positions]
        self.move(self.pos_keys[0])

        # Extra stuff
        self.__class__.instances.append(self)
        logging.info(f'Valve Initiated:\n\tname: {self.name}\n\tport: {self.port}')

    def __repr__(self):
        return f"Valve: {self.name}\n\tport: {self.port}\n\t position: {self.position}"

    def move(self, pos: str):
        """
        Move valve
        :param pos: Position you like to valve to me moved to.
        :return:
        """
        # Check input type
        warning_text = f"Valve(name: {self.name}; port:{self.port}) {pos} is an invalid position provided to move " \
                       f"function. Accepted values are {[i[0] for i in self.positions]} "
        if type(pos) != str:
            warnings.warn(warning_text)
            logging.warning(warning_text)

        # Find index of pos
        try:
            index = self.pos_keys.index(pos)
        except ValueError:
            warnings.warn(warning_text)
            logging.warning(warning_text)
            return

        # Send command to pico
        for _ in range(10):
            self.serial_comm.write(f"v{self.pin}_{self.positions[index][1]}".encode())
            message = self.serial_comm.read_until()
            message = message.decode()
            print(message)
            if message == "ok":
                self.position = pos
                return

        # if the valve doesn't confirm move after 10 calls, stop and report warning
        warning_text = f"Valve(name: {self.name}; port:{self.port}) not responding."
        warnings.warn(warning_text)
        logging.warning(warning_text)
        return None

    def move_next(self):
        """
        Move to next valve position.
        :return:
        """
        index = self.pos_keys.index(self.position)
        if index < len(self.pos_keys):
            index += 1
        else:
            index = 0
        self.move(self.pos_keys[index])

    def move_back(self):
        """
        Move to back one valve position.
        :return:
        """
        index = self.pos_keys.index(self.position)
        if index > 0:
            index -= 1
        else:
            index = len(self.pos_keys)
        self.move(self.pos_keys[index])

if __name__ == '__main__':
    """
    Example code for a single valve.
    You will likely need to change the COM port to match your devices.
    Cycles through positions once.

    Output: Prints to screen the position. 
    """
    from time import sleep

    # # Logging stuff
    # logging.basicConfig(filename=r'.\testing.log',
    #                     level=logging.DEBUG,
    #                     format='%(asctime)s %(message)s',
    #                     datefmt='%m/%d/%Y %I:%M:%S %p')
    # logging.info("\n\n")
    # logging.info("---------------------------------------------------")
    # logging.info("---------------------------------------------------")
    #
    # positions = [
    #     ["P1", 545],
    #     ["P2", 1190],
    #     ["P3", 1820],
    #     ["P4", 2480]
    # ]
    #
    # # Connect to valve
    # V1 = Valve(port="COM8", positions=positions)
    #
    # # Cycle through positions
    # print(V1)
    # for pos in V1.pos_keys:
    #     V1.move(pos)
    #     print(f"Moving to position {pos}.")
    #     sleep(1)
    #
    # print("Done")
    serial_comm = Serial(port="COM9", baudrate=115200, parity=PARITY_EVEN, stopbits=STOPBITS_ONE, timeout=0.1)
    serial_comm.write("v15_0545\r".encode())
    print(serial_comm.read_until())
    serial_comm.read_until()
