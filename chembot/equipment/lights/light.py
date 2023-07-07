import abc
import logging

from chembot.configuration import config
from chembot.equipment.equipment import Equipment


logger = logging.getLogger(config.root_logger_name + ".lights")


class Light(Equipment, abc.ABC):
    """ Base light"""

    def write_on(self):
        """ Turn on light (full power) """
        self.state = self.states.RUNNING
        self._write_on()

    def write_off(self):
        """ Turn off light """
        self._write_off()
        self.state = self.states.STANDBY

    @abc.abstractmethod
    def _write_on(self):
        ...

    @abc.abstractmethod
    def _write_off(self):
        ...
