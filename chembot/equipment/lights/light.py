import abc
import logging

from chembot.configuration import config
from chembot.equipment.equipment import Equipment


logger = logging.getLogger(config.root_logger_name + ".lights")


class Light(Equipment, abc.ABC):
    """ Base light"""

    def write_on(self):
        self.equipment_config.state = self.equipment_config.states.RUNNING
        self._write_on()
        logger.debug(config.log_formatter(self, self.name, "Action | on"))

    def write_off(self):
        self._write_off()
        self.equipment_config.state = self.equipment_config.states.STANDBY
        logger.debug(config.log_formatter(self, self.name, "Action | off"))

    @abc.abstractmethod
    def _write_on(self):
        ...

    @abc.abstractmethod
    def _write_off(self):
        ...
