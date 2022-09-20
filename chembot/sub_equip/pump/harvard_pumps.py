"""
This code is for the Harvard Apparatus PHD 2000 syringe pump.
Pumps receive RS-232 serial commands.

"""

from chembot import logger
from chembot.core_equip.pump import Pump
from chembot.errors import PumpError


def _format_diameter(pump: Pump, diameter: float) -> str:
    # Pump only considers 2 d.p. - anymore are ignored
    diameter_str = str(round(diameter, 2))

    if diameter != float(diameter_str):
        logger.warning(f'{pump.name} diameter truncated to {diameter_str} mm')

    return diameter_str


class HarvardPump(Pump):
    diameter_min = 0.1
    diameter_max = 35

    def __init__(self,
                 serial_line,
                 name: str = "pump",
                 address: int = 0,
                 diameter: float = 0,
                 max_volume: float = 0,
                 max_pull: float = 0,
                 number_syringe: int = 1
                 ):
        super().__init__(serial_line, name, diameter, max_volume, max_pull, number_syringe,
                         control_method=Pump.control_method.flow_rate)
        self._address = None  # '{0:02.0f}'.format(address)
        self.address = address

        self._ping_pump()

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

    def _ping_pump(self):
        """Query model and version number of firmware to check pump is
        OK. Responds with a load of stuff, but the last three characters
        are XXY, where XX is the address and Y is pump status. :, > or <
        when stopped, running forwards, or running backwards. Confirm
        that the address is correct. This acts as a check to see that
        the pump is connected and working."""
        try:
            self.write('VER')
            resp = self.read(17)

            if int(resp[-3:-1]) != int(self.address):
                raise PumpError(f'No response from pump at address {self.address}')
        except PumpError:
            self.serial_line.close()
            raise

    def set_diameter(self, diameter: float):
        """Set syringe diameter (millimetres).
        Pump 11 syringe diameter range is 0.1-35 mm. Note that the pump
        ignores precision greater than 2 decimal places. If more d.p.
        are specified the diameter will be truncated.
        """
        if diameter > self.diameter_max or diameter < self.diameter_min:
            raise PumpError(f'{self.name}: diameter {diameter} mm is out of range')

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
            raise PumpError(f'{self.name}: unknown response to set diameter')

    def write(self, command):
        self.serial_line.write(self.address + command + '\r')

    def read(self, bytes_: int = 5):
        response = self.serial_line.read(bytes_)

        if len(response) == 0:
            raise PumpError('%s: no response to command' % self.name)
        else:
            return response
