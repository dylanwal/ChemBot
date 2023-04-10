import abc
import logging

from unitpy import Quantity

from chembot.configuration import config
from equipment.equipment import EquipmentConfig
from chembot.rabbitmq.rabbitmq_core import RabbitEquipment, RabbitMessage


logger = logging.getLogger(config.root_logger_name + "lights")


class Light(RabbitEquipment):
    def __init__(self, name: str, color: int | Quantity | float | str, communication: str):
        super().__init__(name)
        self.name = name
        self.color = color
        self.communication = communication  # TODO: check for serial in system
        self.power = 0

        self.equipment_config = EquipmentConfig()

    def activate(self):
        logger.info(f"{self.name} activated.")
        self.equipment_config.state = self.equipment_config.states.STANDBY
        RabbitEquipment.activate(self)

    def action_set_power(self, power: int | float | Quantity):
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
        self.rabbit.send(self._set_power(power))
        logger.info(f"Power set to:{power}")

    @abc.abstractmethod
    def _set_power(self, power: int | float | Quantity) -> RabbitMessage:
        ...

    def action_deactivate(self):
        logger.info("Sending shutdown.")
        self.equipment_config.state = self.equipment_config.states.SHUTTING_DOWN
        self._deactivate()
        RabbitEquipment.action_deactivate(self)

    @abc.abstractmethod
    def _deactivate(self):
        ...
