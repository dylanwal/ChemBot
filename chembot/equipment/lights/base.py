import abc
import logging

from unitpy import Quantity

from chembot.configuration import config
from chembot.equipment.equipment import Equipment
from chembot.rabbitmq.messages import RabbitMessage


logger = logging.getLogger(config.root_logger_name + ".lights")


class Light(Equipment):
    """ Base Light"""

    def __init__(self, name: str, color: int | Quantity | float | str, communication: str):
        super().__init__(name)
        self.color = color
        self.communication = communication  # TODO: check for serial in system
        self.power = 0

    def _activate(self):
        pass

    def _deactivate(self):
        pass

    def _get_details(self) -> dict:
        data = {
            "name": self.name,
            "color": self.color,
            "communication": self.communication,
            "power": self.power
        }
        return data

    def set_communication(self, message: RabbitMessage):
        self.communication = message.value

    def set_power(self, message: RabbitMessage):
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
        self._set_power(power)
        logger.info(config.log_formatter(type(self).__name__, self.name, f"Action | power_set: {power}"))

    @abc.abstractmethod
    def _set_power(self, power: int | float | Quantity):
        ...
