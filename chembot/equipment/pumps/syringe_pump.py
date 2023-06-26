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
from chembot.rabbitmq.messages import RabbitMessageAction
from chembot.communication.serial_pico import PicoSerial

logger = logging.getLogger(config.root_logger_name + ".pump")


def calc_pull(diameter: float, volume: float) -> float:
    return volume / (math.pi * (diameter / 2) ** 2)


def calc_volume(diameter: float, pull: float) -> float:
    return math.pi * (diameter / 2) ** 2 * pull


def calc_diameter(volume: float, pull: float) -> float:
    return 2 * math.sqrt(volume / (math.pi * pull))


class PumpControlMethod(enum.Enum):
    flow_rate = 0
    pressure = 1


class SyringePump(Equipment, abc.ABC):
    control_methods = PumpControlMethod

    def __init__(self,
                 name: str,
                 syringe: Syringe,
                 max_pull: Quantity = None,
                 control_method: PumpControlMethod = PumpControlMethod.flow_rate,
                 ):
        super().__init__(name)
        self.syringe = syringe
        self.control_method = control_method
        self._max_pull = max_pull

        # setup everything
        self._volume = 0
        self._flow_rate = 0
        self._target_volume = 0
        self._pull = 0

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__repr__()

    def _activate(self):
        pass
        # set syringe settings
        # ping communication to ensure it is alive
        message = RabbitMessageAction(self.communication, self.name, "read_name")
        self.rabbit.send_and_consume(message, error_out=True)

    def _stop(self):
        pass

    def read_syringe(self):
        pass

    def write_syringe(self, syringe: Syringe):
        pass

    def write_zero(self):
        """"""
        self._pull = 0
        self._volume = 0

    def write_refill(self):
        self._pull = self.max_pull
        self._volume = self._max_volume

    def write_infuse(self):
        pass

    def write_withdraw(self):
        pass
