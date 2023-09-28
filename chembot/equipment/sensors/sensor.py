import abc
import logging

from chembot.configuration import config
from chembot.equipment.equipment import Equipment

logger = logging.getLogger(config.root_logger_name + ".sensor")


class Sensor(Equipment, abc.ABC):

    def __init__(self, name: str):
        super().__init__(name)

    @abc.abstractmethod
    def write_measure(self):
        pass
