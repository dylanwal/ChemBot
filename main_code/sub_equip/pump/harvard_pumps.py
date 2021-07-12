"""
This code is for the Harvard Apparatus PHD 2000 syringe pump.
Pumps receive RS-232 serial commands.

"""
from math import sqrt, pi
import logging

from serial import Serial, STOPBITS_TWO, PARITY_NONE

from main_code import Serializable
from main_code import sig_figs


class SerialLine(Serial):
    """
    Create serial_communication line
    """
    def __init__(self, port):
        Serial.__init__(self, port=port, stopbits=STOPBITS_TWO, parity=PARITY_NONE, timeout=2)
        self.flushOutput()
        self.flushInput()
        logging.info('serial_communication line created on %s', port)


class HarvardPumps(Serializable):

    instances = []

    def __init__(self,
                 serial_line,
                 name: str = "pump",
                 address: int = 0,
                 diameter: float = 0,
                 max_volume: float = 0,
                 max_pull: float = 0
                 ):
        self.__class__.instances.append(self)
        self.syringe_count = 0
        self.syringe_setup = False

        self.serial_line = serial_line
        self.name = name
        logging.info('%s: infusing', self.name)
        self._address = None  # '{0:02.0f}'.format(address)
        self.address = address
        self._diameter = None
        self.diameter = diameter  # units: cm
        self._max_volume = None
        self.max_volume = max_volume  # units: ml
        self._max_pull = None
        self.max_pull = max_pull

        self._volume = None  # units: ml
        self.volume = 0  # units: ml
        self._flow_rate = None  # units: ml/min
        self.flow_rate = 0  # units: ml/min
        self._x = 0
        self.state = "Not Ready"  # Not Ready, Ready, Running, Error

    def __repr__(self):
        return f"Pump: {self.name} (addr.: {self._address}) \n" + \
               f"\tdiameter: {sig_figs(self._diameter, 3)} cm\n" + \
               f"\tmax_volume: {sig_figs(self._max_volume, 3)} ml\n" + \
               f"\tmax_pull: {sig_figs(self._max_pull, 3)} cm\n" + \
               f"current state: {self.state} \n" + \
               f"\tvolume: {sig_figs(self._volume, 3)} ml\n" + \
               f"\tflow_rate: {sig_figs(self._flow_rate, 3)} ml/min\n" + \
               f"\tPosition: {sig_figs(self._x, 3)} ml \n"

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, address):
        """
        Checks performed:
        - Address between [0, 99]
        - Address is an int
        - Address not already taken by another pump
        """
        if 0 <= address <= 99:
            if type(address) is int:
                for pump in self.instances:
                    if pump.address == address:
                        raise ValueError(f"Address {address} already taken by {pump.name}, "
                                         f"so can't be assigned to {self.name}")

                self._address = address
            else:
                raise TypeError("Addresses must be an integer.")
        else:
            raise ValueError("Acceptable addresses are from [0, 99].")

    @property
    def diameter(self):
        return self._diameter

    @diameter.setter
    def diameter(self, diameter):
        if type(diameter) in [float, int]:
            if 0 <= diameter <= 3:
                self._diameter = diameter
                self.syringe_check()
            else:
                raise ValueError("Acceptable addresses are from [0, 3] cm.")
        else:
            raise TypeError("diameter needs to be a float or int value.")

    @property
    def max_volume(self):
        return self._max_volume

    @max_volume.setter
    def max_volume(self, max_volume):
        if type(max_volume) in [float, int]:
            if 0 <= max_volume <= 55:
                self._max_volume = max_volume
                self.syringe_check()
            else:
                raise ValueError("Acceptable addresses are from [0, 55] ml.")
        else:
            raise TypeError("max_volume needs to be a float or int value.")

    @property
    def max_pull(self):
        return self._max_pull

    @max_pull.setter
    def max_pull(self, max_pull):
        if type(max_pull) in [float, int]:
            if 0 <= max_pull <= 15:
                self._max_pull = max_pull
                self.syringe_check()
            else:
                raise ValueError("Acceptable addresses are from [0, 15] cm.")
        else:
            raise TypeError("max_pull needs to be a float or int value.")

    def syringe_check(self):
        """
        This function completes the syringe calculation as only 2 of 3 values are needed.
        V = pi * r**2 * L
        or changes syringe_setup to TRUE if everyting is good
        """

        if not self.syringe_setup:
            if self.syringe_count == 2:
                prop = [self.diameter, self.max_volume, self.max_pull]
                if prop.count(0) == 1:
                    if prop[0] == 0:
                        self.diameter = 2 * sqrt(self.max_volume / (pi*self.max_pull))
                    elif prop[1] == 0:
                        self.max_volume = pi * (self.diameter/2)**2 * self.max_pull
                    elif prop[2] == 0:
                        self.max_pull = self.max_volume / (pi * (self.diameter/2)**2)

                    self.syringe_setup = True

                elif prop.count(0) == 0:
                    diameter = 2 * sqrt(self.max_volume / (pi*self.max_pull))
                    if abs(self.diameter-diameter) <= 0.01:
                        self.syringe_setup = True
                    else:
                        raise ValueError("Syringe diameter, max_volume, max_pull don't match.")
            else:
                self.syringe_count += 1

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, volume):
        self._volume = volume

    @property
    def flow_rate(self):
        return self._flow_rate

    @flow_rate.setter
    def flow_rate(self, flow_rate):
        self._flow_rate = flow_rate

    @property
    def x(self):
        return self._x

    @flow_rate.setter
    def flow_rate(self, flow_rate):
        self._flow_rate = flow_rate


    def zero(self):
        pass
        self._x = 0
        self._volume = 0

    def run(self):
        pass

    def stop(self):
        pass


    def write(self, command):
        self.serialcon.write(self.address + command + '\r')

    def read(self, bytes=5):
        response = self.serialcon.read(bytes)

        if len(response) == 0:
            raise #PumpError('%s: no response to command' % self.name)
        else:
            return response

# def timeout_read(_uart, timeout_ms=20):
#     now = ticks_ms()
#     value = b''
#     while True:
#         if (ticks_ms() - now) > timeout_ms:
#             break
#         if _uart.any():
#             value = value + _uart.read(1)
#             now = ticks_ms()
#     return value
#
#
# def polling(_uart):
#     """
#     This function is to determine what controls we have acess to.
#     para: _uart: uart object
#     return: active: list with active pump ids
#     """
#     active = []
#     for i in range(2):  # looping over pump
#         responce = 0
#         for ii in range(3):  # giving each pump 3 attempts to reply
#             message = str(i + 1) + "R"  # destination + acknowledgement
#             message = add_checksum(message)
#             message = message + '\r'
#
#             if i == 0:  # A [CR] must start the network.
#                 message = '\r' + message
#
#             # ping pump
#             message = '\r1R5D\r'
#             print(message)
#             _uart.write(message)
#
#             # wait for reply
#             responce = timeout_read(_uart, timeout_ms=20)
#             print(responce)
#
#             if responce:
#                 active.append(i + 1)
#                 break
#             sleep(0.1)
#
#     return active





if __name__ == "__main__":
    # uart = UART(0, 9600, bits=8, parity=None, stop=2)
    #
    # address = 1
    # message = '{0:02.0f}'.format(address) + 'VER' + '\r'
    # # message = '{0:02.0f}'.format(address) + 'RUN' + '\r'
    # # message = '{0:02.0f}'.format(address) + 'ULM' + '1' + '\r'
    # print("sent message: " + str(message))
    # uart.write(message)
    # responce = timeout_read(uart, timeout_ms=200)
    # print("recieved message: " + str(responce))
    serial = SerialLine(port="COM3")
    a = HarvardPumps(serial_line=serial, name="syr_pump_rxn1", address=0, diameter=1, max_volume=10)
    b = HarvardPumps(serial_line=serial, name="syr_pump_rxn2", address=1, max_pull=6, max_volume=1)

    print(a)
    print(b)
    print(a.as_dict())
