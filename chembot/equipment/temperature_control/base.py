import abc
import logging

from unitpy import Quantity

from chembot.configuration import config
from chembot.equipment.equipment import Equipment


logger = logging.getLogger(config.root_logger_name + ".lights")


class TempControl(Equipment, abc.ABC):
    """ Base light"""

    @abc.abstractmethod
    def write_set_point(self, temperature: Quantity):
        """ write set point temperature """

    @abc.abstractmethod
    def read_set_point(self) -> Quantity:
        """ Turn off light """

    @abc.abstractmethod
    def read_temperature(self) -> Quantity:
        """ Turn off light """

