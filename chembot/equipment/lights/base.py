import abc
import logging
from abc import ABC

from unitpy import Quantity

from chembot.configuration import config
from chembot.equipment.equipment import Equipment
from chembot.rabbitmq.messages import RabbitMessage


logger = logging.getLogger(config.root_logger_name + ".lights")


class Light(Equipment, ABC):
    """ Base Light"""


class LightAdjustablePower(Light, ABC):
    """ Base Light"""
    def __init__(self, name: str, color: int | Quantity | float | str):
        super().__init__(name)
        self.color = color
        self.power = 0

    def _activate(self):
        pass

    def _deactivate(self):
        pass

    def write_power(self, message: RabbitMessage):
        """

        Parameters
        ----------
        message

        Returns
        -------

        """
        power = message.value
        if isinstance(power, int) or isinstance(power, float):
            if power > 0:
                self.equipment_config.state = self.equipment_config.states.RUNNING
            elif power == 0:
                self.equipment_config.state = self.equipment_config.states.STANDBY
        if isinstance(power, Quantity):
            if power.v > 0:
                self.equipment_config.state = self.equipment_config.states.RUNNING
            elif power.v == 0:
                self.equipment_config.state = self.equipment_config.states.STANDBY

        self.power = power
        self._write_power(power)
        logger.info(config.log_formatter(type(self).__name__, self.name, f"Action | power_set: {power}"))

    @abc.abstractmethod
    def _write_power(self, power: int | float | Quantity):
        ...
