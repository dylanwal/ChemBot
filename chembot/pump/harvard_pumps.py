import enum
import math
import time

from chembot import event_scheduler, logger
from chembot.pump.base import Pump
from chembot.pump.flow_profile import PumpFlowProfile
from chembot.communication.serial_ import Serial
from chembot.errors import EquipmentError


class PumpHarvardStates(enum.Enum):
    stopped = ":"
    running_forward = ">"
    running_backward = "<"
    stalled = "*"


def remove_crud(string: str) -> str:
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


def _format_flow_rate(pump: Pump, flow_rate: int | float) -> str:
    flow_rate = str(flow_rate)

    if len(flow_rate) > 5:
        flow_rate = flow_rate[0:5]
        logger.warning(f'{pump.name} flow rate truncated to {flow_rate} uL/min')

    return remove_crud(flow_rate)


def remove_string_formatting_char(string: str) -> str:
    return ''.join(s for s in string if 31 < ord(s) < 126)


class PumpHarvard(Pump):
    """
    This code is for the Harvard Apparatus PHD 2000 syringe pump.
    Pumps receive RS-232 serial commands.

    """
    pull_rate_min = 0.00002  # cm/min
    pull_rate_max = 19.0  # cm/min
    baud_rates = [1200, 2400, 9600, 19200]

    _address_in_use = set()

    def __init__(
            self,
            serial_line: Serial,
            address: int,
            diameter: int | float,  # units: mm
            name: str = None,
            max_volume: float = None,  # units: ml
            max_pull: float = None,  # units: cm
    ):
        super().__init__(name, diameter, max_volume, max_pull,
                         control_method=Pump.control_methods.flow_rate)
        if name is None:
            self.name = f"{type(self).__name__} (id: {self.id_})"
        self.serial_line = serial_line
        self._address = None
        self.address = address

        self.ping_pump()
        self.diameter = diameter

    @property
    def max_flow_rate(self) -> float:
        """ ml/min """
        return math.pi * (self.diameter / 2)**2 * self.pull_rate_max

    @property
    def min_flow_rate(self) -> float:
        """ ml/min """
        return math.pi * (self.diameter / 2)**2 * self.pull_rate_min

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
        """
        Write command to serial line.
        Should not be used directly, as it is not thread safe; use self._write_read

        Parameters
        ----------
        message: str
            message to send to pump

        """
        self.serial_line.write(self.address + message + '\r')

    def _read(self, bytes_: int = 5) -> str:
        """
        Read response on serial line.
        Should not be used directly, as it is not thread safe; use self._write_read

        Parameters
        ----------
        bytes_: int
            how many bytes you want to read

        Returns
        -------
        response: str

        """
        response = self.serial_line.read(bytes_)
        if response is None or len(response) == 0:
            raise EquipmentError(self, 'No response to command.')
        else:
            return response

    def _write_read(self, message: str, bytes_: int = 5) -> list:
        """
        The pump operates in a 'write' 'response' format; so methods are combined.
        Multiple pumps can use the same serial line so threading lock is acquired and released.

        Parameters
        ----------
        message: str
            message to send to pump
        bytes_: int
            how many bytes you want to read

        Returns
        -------
        response: str

        """
        self.serial_line.lock.acquire()
        self._write(message)
        response = self._read(bytes_)
        self.serial_line.lock.release()

        return response.replace('\n', " ").replace('\r', " ").split()

    def ping_pump(self):
        """Query model and version number of firmware to check pump is
        OK. Responds with a load of stuff, but the last three characters
        are XXY, where XX is the address and Y is pump status. :, > or <
        when stopped, running forwards, or running backwards. Confirm
        that the address is correct. This acts as a check to see that
        the pump is connected and working."""
        response = self._write_read('VER', 17)

        # check response
        if int(response[1][:-1]) != int(self.address):
            self.serial_line.close()
            raise EquipmentError(self, f'No response from pump at address {self.address}\n Check the following: '
                                       f'\n\t1. All pumps have unique addresses\n\t2. All pumps have the same '
                                       f'baud rates.')

    def _diameter_setter(self, diameter: int | float):
        super()._diameter_setter(diameter)
        self._set_diameter(diameter)

    def _set_diameter(self, diameter: float):
        """Set syringe diameter (millimetres).
        Pump 11 syringe diameter range is 0.1-35 mm. Note that the pump
        ignores precision greater than 2 decimal places. If more d.p.
        are specified the diameter will be truncated.
        """
        # Send command
        response = self._write_read('MMD' + _format_diameter(self, diameter), 5)

        # check response
        if not (response[0][-1] == ':' or response[0][-1] == '<' or response[0][-1] == '>'):
            raise EquipmentError(self, f'Unknown response to set diameter.')

        # Check diameter was set accurately
        if returned_diameter := self.check_diameter() != diameter:
            raise EquipmentError(self, f'Set diameter ({diameter} mm) does not match diameter'
                                       f' returned by pump ({returned_diameter} mm)')

        # log update
        logger.info(f'{self.name}: diameter set to {self.diameter} mm')

    def check_diameter(self) -> float:
        response = self._write_read('DIA', 15)
        try:
            return float(response[0])
        except ValueError:
            raise EquipmentError(self, f'Unknown response to check diameter')

    def _set_flow_rate(self, flow_rate: float | int):
        """Set flow rate (microlitres per minute).
        Flow rate is converted to a string. Pump 11 requires it to have
        a maximum field width of 5, e.g. "XXXX." or "X.XXX". Greater
        precision will be truncated.
        The pump will tell you if the specified flow rate is out of
        range. This depends on the syringe diameter. See Pump 11 manual.
        """
        if not (self.min_flow_rate <= flow_rate <= self.max_flow_rate):
            raise EquipmentError(self, f"Flow rate outside of valid range. Requested: {flow_rate}, "
                                       f"Valid Range: {self.min_flow_rate} -> {self.max_flow_rate}")

        formatted_flow_rate = _format_flow_rate(self, flow_rate)
        response = self._write_read('ULM' + formatted_flow_rate, 5)

        # check response
        if not (response[0][-1] == ':' or response[0][-1] == '<' or response[0][-1] == '>'):
            raise EquipmentError(self, f'Unknown response to set flow rate.')

        # Flow rate was sent, check it was set correctly
        if returned_flow_rate := self.check_flow_rate() != float(formatted_flow_rate):
            raise EquipmentError(self, f"set flow rate ({flow_rate} uL/min) does not match"
                                       f'flow rate returned by pump ({returned_flow_rate} uL/min)')

        self._flow_rate = flow_rate
        logger.info(f"{self.name}: flow rate set to {formatted_flow_rate} uL/min")

    def check_flow_rate(self) -> float:
        response = self._write_read('RAT', 15)
        try:
            return float(response[0])
        except ValueError:
            if 'OOR' in response:
                raise EquipmentError(self, 'Flow rate is out of range')

            raise EquipmentError(self, f"Unknown response to 'check flow rate'.")

    def _set_target_volume(self, target_volume: int | float):
        """Set the target volume to infuse or withdraw (microlitres)."""
        response = self._write_read('MLT' + str(target_volume), 5)

        # response should be CRLFXX:, CRLFXX>, CRLFXX< where XX is address
        # Pump11 replies with leading zeros, e.g. 03, but PHD2000 misbehaves and
        # returns without and gives an extra CR. Use int() to deal with
        if not (response[0][-1] == ':' or response[0][-1] == '<' or response[0][-1] == '>'):
            raise EquipmentError(self, f'Unknown response to set flow rate.')

        self._target_volume = float(target_volume)
        logger.info(f"{self.name}: target volume set to {target_volume} uL")

    def check_target_volume(self) -> float:
        response = self._write_read('TAR', 15)
        try:
            return float(response[0])
        except ValueError:
            raise EquipmentError(self, f"Unknown response to 'check target volume'.")

    def check_infused_volume(self) -> float:
        response = self._write_read('VOL', 15)
        try:
            return float(response[0])
        except ValueError:
            raise EquipmentError(self, f"Unknown response to 'check target volume'.")

    def infuse(self, flow_rate: int | float, volume: int | float = None):
        """
        Start infusing pump.

        Parameters
        ----------
        flow_rate: int | float
            flow rate (microlitres per minute)
        volume: int | float
            volume to be added (microlitres)

        """
        # set up everything
        self._set_flow_rate(flow_rate)
        if volume is None:
            if self.max_volume is not None:
                volume = self.max_volume
            else:
                volume = 1_000_000  # large number to ensure it adds everything
        self._set_target_volume(volume)

        # start run
        response = self._write_read('RUN', 5)
        if response[1][-1] == '<':  # wrong direction
            response = self._write_read('REV', 5)

        if response[1][-1] != '>':
            raise EquipmentError(self, "Unknown response to 'infuse'")

        logger.info(f"{self.name}: infusing")

    def withdraw(self, flow_rate: int | float, volume: int | float = None):
        """
        Start withdrawing pump.

        Parameters
        ----------
        flow_rate: int | float
            flow rate (microlitres per minute)
        volume: int | float
            volume to be added (microlitres)

        """
        # set up everything
        self._set_flow_rate(flow_rate)
        if volume is None:
            if self.max_volume is not None:
                volume = self.max_volume - self.volume
            else:
                logger.warning(f"withdraw started on pump {self.id_} with no stop.")
                volume = 1_000_000  # large number to ensure it adds everything
        self._set_target_volume(volume)

        # start run
        self._set_flow_rate(flow_rate)
        response = self._write_read('RUN', 5)
        if response[1][-1] == '>':  # wrong direction
            response = self._write_read('REV', 5)

        if response[1][-1] != '<':
            raise EquipmentError(self, "Unknown response to 'withdraw'.")

        logger.info(f"{self.name}: withdrawing")

    def stop(self):
        """ Stop pump. """
        response = self._write_read('STP', 5)
        if response[0][-1] != ':':
            raise EquipmentError(self, "Unknown response to 'stop'.")

        logger.info(f'{self.name}: stopped')

    def zero(self):
        self.infuse(flow_rate=self.max_flow_rate * 0.5)

    def fill(self):
        self.withdraw(flow_rate=self.max_flow_rate * 0.5)

    def run(self, flow_profile: PumpFlowProfile, start_time: int | float = 0):
        if start_time is None:
            start_time = time.time()

        # first event


def local_run_two_pumps():
    from chembot.communication import Serial
    serial_line = Serial("COM5", baud_rate=9600, parity=Serial.ParityOptions.none, stop_bits=2, bytes_=8, timeout=1)

    pump = PumpHarvard(
        serial_line,
        address=0,
        diameter=1,
        max_volume=10,
    )
    pump2 = PumpHarvard(
        serial_line,
        address=1,
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

    pump.run(flow_profile)
    pump2.run(flow_profile)


def local_flow_profile():
    from chembot.communication import Serial
    serial_line = Serial("COM5", baud_rate=9600, parity=Serial.ParityOptions.none, stop_bits=2, bytes_=8, timeout=1)

    pump = PumpHarvard(
        serial_line,
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
    pump.run(flow_profile)


def local_run_single():
    from chembot.communication import Serial
    serial_line = Serial("COM5", baud_rate=9600, parity=Serial.ParityOptions.none, stop_bits=2, bytes_=8, timeout=1)

    pump = PumpHarvard(
        serial_line,
        address=0,
        diameter=14.2,
        max_volume=10000,
    )
    pump.zero()
    # pump.withdraw(1, 1)
    # pump.infuse(1, 1)


if __name__ == '__main__':
    local_run_single()
