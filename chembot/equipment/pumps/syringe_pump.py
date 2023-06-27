"""

syringe pump queues
    write to:
    * error
    * status
    * communication line (serial line to pump)
    read from:
    * SyringePump_i

logger

"""

import abc
import math
import enum
import logging

from unitpy import Quantity, Unit

from chembot.configuration import config
from chembot.equipment.equipment import Equipment
from chembot.equipment.pumps.syringes import Syringe
from chembot.utils.unit_validation import validate_quantity

logger = logging.getLogger(config.root_logger_name + ".pump")


class PumpControlMethod(enum.Enum):
    flow_rate = 0
    pressure = 1


class SyringePumpStatus(enum.Enum):
    STANDBY = "standby"
    INFUSE = "infuse"
    WITHDRAW = "withdraw"
    STALLED = "stalled"
    TARGET_REACHED = "target_reached"


class SyringePump(Equipment, abc.ABC):
    control_methods = PumpControlMethod

    def __init__(self,
                 name: str,
                 syringe: Syringe,
                 max_pull: Quantity = None,
                 max_pull_rate: Quantity = None,
                 control_method: PumpControlMethod = PumpControlMethod.flow_rate,
                 ):
        super().__init__(name)
        self.syringe = syringe
        self.control_method = control_method
        self._max_pull = max_pull
        self._max_pull_rate = max_pull_rate

        # setup current values
        self._pump_state: SyringePumpStatus | None = None
        self._volume: Quantity | None = None
        self._volume_displace: Quantity | None = None
        self._flow_rate: Quantity | None = None
        self._target_volume: Quantity | None = None
        self._running_time: Quantity | None = None
        self._end_time: Quantity | None = None
        self._pull: Quantity | None = None

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__repr__()

    def _activate(self):
        self._pump_state = SyringePumpStatus.STANDBY
        self.write_empty()

    def _within_max_pull(self, volume: Quantity, direction: bool = True) -> bool:
        pull = self.compute_pull(volume, self.syringe.diameter)
        if not direction:
            pull = -1 * direction

        total_pull = self._pull + pull
        if 0 < total_pull.v:
            return False
        if self._max_pull is not None and total_pull > self._max_pull:
            return False
        if total_pull > self.syringe.pull:
            return False

        return True

    def read_syringe(self) -> Syringe:
        """ get syringe """
        return self.syringe

    def write_syringe(self, syringe: Syringe):
        """ set syringe """
        self.syringe = syringe

    def write_empty(self, flow_rate: Quantity = None):
        """ empty syringe """
        if flow_rate is None:
            flow_rate = self.syringe.default_flow_rate
        self.write_infuse(self.syringe.volume, flow_rate, ignore_stall=True)
        self._pull = 0 * Unit.m
        self._volume = 0 * Unit("ml/min")

    def write_refill(self, flow_rate: Quantity = None):
        """ refill syringe to max volume """
        if flow_rate is None:
            flow_rate = self.syringe.default_flow_rate

        volume = self.syringe.volume - self._volume
        self.write_withdraw(volume, flow_rate, ignore_limit=True)

    def write_infuse(self, volume: Quantity, flow_rate: Quantity, ignore_stall: bool = False):
        """
        Run infuse liquid.

        Parameters
        ----------
        volume:
            volume to be infused
        flow_rate:
            flow rate
        ignore_stall:
            True: don't throw an error if the pump stops due to stall
            False: will throw an error
        """
        validate_quantity(volume, Syringe.volume_dimensionality, "volume", True)
        validate_quantity(volume, Syringe.volume_dimensionality, "flow_rate")
        if not ignore_stall and self._within_max_pull(volume):
            raise ValueError("Stall expected as pull too large. Lower volume infused or ignore_stall=False")

        self._write_infuse(volume, flow_rate)
        self.watchdog.set_watchdog()  # TODO: check completion

        self.state = self.states.RUNNING
        self._pump_state = SyringePumpStatus.INFUSE
        self._volume_displace = 0 * volume.unit
        self._flow_rate = flow_rate
        self._target_volume = volume
        self._running_time = 0 * Unit.s
        self._end_time = self.compute_run_time(volume, flow_rate)

    def write_withdraw(self, volume: Quantity, flow_rate: Quantity, ignore_limit: bool = False):
        # check current pull and see if there volume will exceed max limit
        validate_quantity(volume, Syringe.volume_dimensionality, "volume", True)
        validate_quantity(volume, Syringe.volume_dimensionality, "flow_rate")
        if not self._within_max_pull(volume):
            raise ValueError("Too much withdraw volume requested. Lower volume withdraw")

        self._write_infuse(volume, flow_rate)
        self.watchdog.set_watchdog()  # TODO: check completion

        self.state = self.states.RUNNING
        self._pump_state = SyringePumpStatus.WITHDRAW
        self._volume_displace = 0 * volume.unit
        self._flow_rate = flow_rate
        self._target_volume = volume
        self._running_time = 0 * Unit.s
        self._end_time = self.compute_run_time(volume, flow_rate)

    @abc.abstractmethod
    def _write_infuse(self, volume: Quantity, flow_rate: Quantity):
        ...

    @abc.abstractmethod
    def _write_withdraw(self, volume: Quantity, flow_rate: Quantity):
        ...

    @staticmethod
    def compute_run_time(volume: Quantity, flow_rate: Quantity) -> Quantity:
        validate_quantity(volume, Syringe.volume_dimensionality, "volume", True)
        validate_quantity(volume, Syringe.flow_rate_dimensionality, "flow_rate", True)
        return abs(volume/flow_rate)

    @staticmethod
    def compute_pull(diameter: Quantity, volume: Quantity) -> Quantity:
        validate_quantity(diameter, Syringe.diameter_dimensionality, "diameter", True)
        validate_quantity(volume, Syringe.volume_dimensionality, "volume", True)
        return volume / (math.pi * (diameter / 2) ** 2)

    @staticmethod
    def compute_volume(diameter: Quantity, pull: Quantity) -> Quantity:
        validate_quantity(diameter, Syringe.volume_dimensionality, "diameter", True)
        validate_quantity(pull, Syringe.pull_dimensionality, "pull", True)
        return math.pi * (diameter / 2) ** 2 * pull

    @staticmethod
    def compute_diameter(volume: Quantity, pull: Quantity) -> Quantity:
        validate_quantity(pull, Syringe.pull_dimensionality, "pull", True)
        validate_quantity(volume, Syringe.volume_dimensionality, "volume", True)
        return 2 * (volume / (math.pi * pull))**(1/2)
