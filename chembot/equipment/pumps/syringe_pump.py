
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


class SyringeState:
    """ capture current pump values """
    __slots__ = ("state", "_volume_in_syringe", "volume_displace", "target_volume", "flow_rate", "running_time",
                 "end_time", "max_volume", "syringe", "_max_pull")

    def __init__(self, syringe: Syringe, max_pull: Quantity = None):
        self.state: SyringePumpStatus | None = None
        self._volume_in_syringe: Quantity | None = None
        self.volume_displace: Quantity | None = None
        self.target_volume: Quantity | None = None
        self.flow_rate: Quantity | None = None
        self.running_time: Quantity | None = None
        self.end_time: Quantity | None = None
        self.syringe = syringe
        self._max_pull = max_pull

    @property
    def volume_in_syringe(self) -> Quantity | None:
        return self._volume_in_syringe

    @volume_in_syringe.setter
    def volume_in_syringe(self, volume_in_syringe: Quantity):
        self._volume_in_syringe = volume_in_syringe
        if self._volume_in_syringe.v < 0:
            logger.error("Volume in syringe went negative!")
        if self._volume_in_syringe > self.max_volume:
            logger.error("Volume in syringe over max!")

    @property
    def pull(self) -> Quantity | None:
        # compute from volume
        return SyringePump.compute_pull(self.syringe.diameter, self.volume_in_syringe)

    @property
    def max_pull(self) -> Quantity:
        if self._max_pull is not None and self.syringe.pull > self._max_pull:
            return self._max_pull
        return self.syringe.pull

    def within_max_pull(self, delta_pull: Quantity, direction: bool = True) -> bool:
        if not direction:
            delta_pull = -1 * direction

        total_pull = self.pull + delta_pull
        if 0 < total_pull.v:
            return False
        if total_pull > self.max_pull:
            return False

        return True


class SyringePump(Equipment, abc.ABC):
    control_methods = PumpControlMethod
    pump_states = SyringePumpStatus

    def __init__(self,
                 name: str,
                 syringe: Syringe,
                 max_pull: Quantity = None,
                 control_method: PumpControlMethod = PumpControlMethod.flow_rate,
                 ):
        super().__init__(name)
        self.syringe = syringe
        self.control_method = control_method
        self.pump_state = SyringeState(self.syringe, max_pull)
        # TODO: check max and min flow rates

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__repr__()

    def read_syringe(self) -> Syringe:
        """ get syringe """
        return self.syringe

    def write_syringe(self, syringe: Syringe):
        """ set syringe """
        self.syringe = syringe

    @staticmethod
    def compute_run_time(volume: Quantity, flow_rate: Quantity) -> Quantity:
        validate_quantity(volume, Syringe.volume_dimensionality, "volume", True)
        validate_quantity(flow_rate, Syringe.flow_rate_dimensionality, "flow_rate", True)
        duration = abs(volume/flow_rate)
        return duration

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
