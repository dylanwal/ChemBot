"""
This code is for the Harvard Apparatus PHD 2000 syringe pumps.
Pumps receive RS-232 serial commands.

"""
from math import sqrt, pi

from serial import Serial

from main_code.utils.serializable import Serializable


class harvard_pumps(Serializable):

    instances = []

    def __init__(self,
                 name: str = "pump",
                 address: int = 0,
                 diameter: float = 0,
                 max_volume: float = 0,
                 max_pull: float = 0
                 ):
        self.__class__.instances.append(self)
        self._name = None
        self.name = name
        self._address = None  # '{0:02.0f}'.format(address)
        self.address = address
        self._diameter = None
        self.diameter = diameter  # units: cm
        self._max_volume = None
        self.max_volume = max_volume  # units: ml
        self._max_pull = None
        self.max_pull = max_pull
        self._syringe_setup = False

        self._volume = None  # units: ml
        self._flow_rate = None  # units: ml/min
        self._x = None
        self._state = "Not Ready"

    def __repr__(self):
        return f"Pump: {self._name} (addr.: {self._address}) \n" + \
               f"\tdiameter: {self._diameter} cm\n" + \
               f"\tmax_volume: {self._max_volume} ml\n" + \
               f"\tmax_pull: {self._max_pull} cm\n" + \
               f"current state: {self._state} \n" + \
               f"\tvolume: {self._volume} ml\n" + \
               f"\tflow_rate: {self._flow_rate} ml/min\n" + \
               f"\tPosition: {self._x} ml \n"

    @property
    def name(self):
        return self._address

    @name.setter
    def name(self, name):
        if type(name) is str:
            self._name = name
        else:
            raise TypeError("Name must be an string.")

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
                        raise ValueError(f"Address {address} already taken by {pump._name}, "
                                         f"so can't be assigned to {self._name}")

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
        if 0 <= diameter <= 3:
            self._diameter = diameter
            self.syringe_check()
        else:
            raise ValueError("Acceptable addresses are from [0, 3] cm.")

    @property
    def max_volume(self):
        return self._max_volume

    @max_volume.setter
    def max_volume(self, max_volume):
        self._max_volume = max_volume

    @property
    def max_pull(self):
        return self._max_pull

    @max_pull.setter
    def max_pull(self, max_pull):
        self._max_pull = max_pull

    def syringe_check(self):
        """
        This function completes the syringe calculation as only 2 of 3 values are needed.
        V = pi * r**2 * L
        or changes _syringe_setup to TRUE if everyting is good
        """
        trio = [self.diameter, self.max_volume, self.max_pull]
        if not self._syringe_setup:
            if trio.count(0) == 1:
                if trio[0] == 0:
                    self.diameter = 2 * sqrt(self.max_volume / (pi*self.max_pull))
                elif trio[1] == 0:
                    self.max_volume = pi * (self.diameter/2)**2 * self.max_pull
                elif trio[2] == 0:
                    self.max_pull = self.max_volume / (pi * (self.diameter/2)**2)

                self._syringe_setup = True

            elif trio.count(0) == 0:
                diameter = 2 * sqrt(self.max_volume / (pi*self.max_pull))
                if abs(self.diameter-diameter) == 0.01:
                    self._syringe_setup = True
                else:
                    raise ValueError("Syringe diameter, max_volume, max_pull don't match.")


    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, volume):
        self._volume = volume

    @property
    def x(self):
        return self._x

    @property
    def state(self):
        return self._state



    def zero(self):
        pass
        self._x = 0
        self._volume = 0

    def run(self):
        pass

    def stop(self):
        pass

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
#     for i in range(2):  # looping over pumps
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
    a = harvard_pumps(name="syr_pump_rxn1", address=0, diameter=1, max_volume=10)
    b = harvard_pumps(name="syr_pump_rxn2", address=1, diameter=1, max_volume=10)

    print(a)
    #print(a.as_dict())
