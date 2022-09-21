import enum

from chembot import logger
from chembot.pump.base import Pump
from chembot.pump.flow_profile import PumpFlowProfile
from chembot.communication.serial_ import Serial
from chembot.errors import EquipmentError


class PumpHarvardStates(enum.Enum):
    stopped = ":"
    running_forward = ">"
    running_backward = "<"
    stalled = "*"


def remove_crud(string):
    """Return string without useless information.
     Return string with trailing zeros after a decimal place, trailing
     decimal points, and leading and trailing spaces removed.
     """
    if "." in string:
        string = string.rstrip('0')

    string = string.lstrip('0 ')
    string = string.rstrip(' .')

    return string


def _format_diameter(pump: Pump, diameter: float) -> str:
    # Pump only considers 2 d.p. - anymore are ignored
    diameter_str = str(round(diameter, 2))

    if diameter != float(diameter_str):
        logger.warning(f'{pump.name} diameter truncated to {diameter_str} mm')

    return diameter_str


class PumpHarvard(Pump):
    """
    This code is for the Harvard Apparatus PHD 2000 syringe pump.
    Pumps receive RS-232 serial commands.

    """
    pull_rate_min = 0.00002  # cm/min
    pull_rate_max = 19.0  # cm/min
    baud_rates = [1200, 2400, 9600, 19200]

    _address_in_use = set()

    def __init__(self,
                 serial_line: Serial,
                 name: str = None,
                 address: int = 0,
                 diameter: float = 0,
                 max_volume: float = 0,
                 max_pull: float = 0,
                 ):
        super().__init__(serial_line, name, diameter, max_volume, max_pull,
                         control_method=Pump.control_methods.flow_rate)
        self._address = None
        self.address = address

        self._ping_pump()

    @property
    def address(self) -> str:
        return self._address

    @address.setter
    def address(self, address: int):
        """
        Checks performed:
        - Address between [0, 99]
        - Address is an int
        - Address not already taken by another pump
        """
        if 0 > address or address > 99:
            raise EquipmentError(self, "Acceptable addresses are from [0, 99].")

        if type(address) is not int:
            raise EquipmentError(self, "Addresses must be an integer.")

        if address in self._address_in_use:
            raise EquipmentError(self, f"Address {address} already taken, so can't be assigned to {self.name}")

        self._address = '{0:02.0f}'.format(address)
        self._address_in_use.add(address)

    def _write(self, message: str):
        self.serial_line.write(self.address + message + '\r')

    def _read(self, bytes_: int = 5) -> str:
        response = self.serial_line.read(bytes_)
        print(response)
        if response is None or len(response) == 0:
            raise EquipmentError(self, 'No response to command.')
        else:
            return response

    def _ping_pump(self):
        """Query model and version number of firmware to check pump is
        OK. Responds with a load of stuff, but the last three characters
        are XXY, where XX is the address and Y is pump status. :, > or <
        when stopped, running forwards, or running backwards. Confirm
        that the address is correct. This acts as a check to see that
        the pump is connected and working."""
        try:
            self._write('VER')
            message = self._read(17)
            print(message)
            if int(message[-3:-1]) != int(self.address):
                raise EquipmentError(self, f'No response from pump at address {self.address}\n Check the following: '
                                           f'\n\t1. All pumps have unique addresses\n\t2. All pumps have the same '
                                           f'baud rates.')
        except EquipmentError:
            self.serial_line.close()
            raise

    def _set_diameter(self, diameter: float):
        """Set syringe diameter (millimetres).
        Pump 11 syringe diameter range is 0.1-35 mm. Note that the pump
        ignores precision greater than 2 decimal places. If more d.p.
        are specified the diameter will be truncated.
        """
        # Send command
        self.write('MMD' + _format_diameter(self, diameter))
        response = self.read(5)

        # Pump replies with address and status (:, < or >)
        if (response[-1] == ':' or response[-1] == '<' or response[-1] == '>'):
            # check if diameter has been set correctly
            self.write('DIA')
            resp = self.read(15)
            returned_diameter = remove_crud(resp[3:9])

            # Check diameter was set accurately
            if returned_diameter != diameter:
                logger.error(f'{self.name}: set diameter ({diameter} mm) does not match diameter'
                              f' returned by pump ({returned_diameter} mm)')
            elif returned_diameter == diameter:
                self.diameter = float(returned_diameter)
                logger.info(f'{self.name}: diameter set to {self.diameter} mm')
        else:
            raise EquipmentError(self, f'Unknown response to set diameter')

    def run(self):
        pass


def local_run():
    from chembot.communication import Serial

    pump = PumpHarvard(
        serial_line=Serial("COM5", baud_rate=9600, parity=Serial.ParityOptions.none.value, stop_bits=2, bytes_=8,
                           timeout=1),
        address=0,
        diameter=1,
        max_volume=10,
    )

    flow_profile = PumpFlowProfile(
        (
            (0, 0),
            (1, 1),
            (2, 1),
            (3, 2),
            (4, 0)
        )
    )
    pump.set_flow_profile(flow_profile)
    pump.run()


if __name__ == '__main__':
    local_run()
