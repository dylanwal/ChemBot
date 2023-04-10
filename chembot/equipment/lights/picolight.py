import logging

import numpy as np
from scipy.optimize import root
from unitpy import Quantity

from chembot.configuration import config
from equipment.lights.base import Light
from chembot.rabbitmq.rabbitmq_core import RabbitEquipment, RabbitMessage
from chembot.utils.pico_checks import check_GPIO_pins

logger = logging.getLogger(config.root_logger_name + "lights")


class LightPico(Light):
    """
    LigthPico

    """

    def __init__(self,
                 name: str,
                 color: int | Quantity | float | str,
                 communication: str,
                 pin: int,
                 frequency: int = 300,
                 conversion: callable = None
                 ):
        self.conversion = conversion
        self._pin = None
        self.pin = pin
        self.frequency = frequency
        self.power_range = (0, 100)
        self.power_quantity_range = (self.conversion(0), self.conversion(100))
        super().__init__(name, color, communication)


    @property
    def pin(self) -> int:
        return self._pin

    @pin.setter
    def pin(self, pin: int):
        check_GPIO_pins(pin)
        self._pin = pin

    def _get_details(self) -> dict:
        data = {
            "name": self.name,
            "color": self.color,
            "communication": self.communication,
            "pin": self.pin,
            "frequency": self.frequency,
            "power": self.power

        }
        return data

    def _set_power(self, power: int | float | Quantity) -> RabbitMessage:
        return RabbitMessage(self.communication, self.name, "write", self._get_message_to_set_power(power),
                             {"reply": True, "send_reply": False, "reply_action": "read_until"})

    def _get_message_to_set_power(self, power: int | float | Quantity) -> str:
        if isinstance(power, Quantity):
            def conversion(x: int | float) -> int | float:
                return (self.conversion(x) - power).value

            result = root(conversion, x0=np.array([1]))
            power = round(result.x[0])

        elif isinstance(power, float):
            power = round(float)

        if not (self.power_range[0] < power < self.power_range[1]):
            raise ValueError("Power outside acceptable range.")

        return "l" + str(self.pin).zfill(2) + str(self.frequency).zfill(4) + str(power).zfill(3) + "\r"

    def _deactivate(self):
        message = RabbitMessage(self.conversion, self.name, "write", "e\r")
        self.rabbit.send(message)  # TODO: set timer and wait for confirmation before shutting down
