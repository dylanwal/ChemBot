import logging

import numpy as np
from scipy.optimize import root
from unitpy import Quantity

from chembot.configuration import config
from equipment.lights.base import Light
from chembot.rabbitmq.core import RabbitMessage
from chembot.utils.pico_checks import check_GPIO_pins

logger = logging.getLogger(config.root_logger_name + ".lights")


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
        self._frequency = None
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

    @property
    def frequency(self) -> int:
        return self._frequency

    @frequency.setter
    def frequency(self, frequency: int):
        if not isinstance(frequency, int):
            raise TypeError("'frequency' must be an integer.")

        if not (100 < frequency < 50_000):
            raise ValueError("'frequency' must be between [100, 50_000]")

        self._frequency = frequency

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

    def _deactivate(self):
        # write to pico
        message = RabbitMessage(self.communication, self.name, "write", "e\r")
        self.rabbit.send(message)

        # get reply
        message = RabbitMessage(self.communication, self.name, "read_until", self._get_message())
        self.rabbit.send(message)
        self._set_reply_alarm(5, self._deactivate_callback)

    def _deactivate_callback(self, message: RabbitMessage):
        if message.value == "e":
            logger.debug("Reply to set power received.")
        else:
            self.rabbit.send_error("WrongReply", message.to_str())

    def set_pin(self, message: RabbitMessage):
        self.pin = message.value
        self._send_message()

    def set_frequency(self, message: RabbitMessage):
        self.frequency = message.value
        self._send_message()

    def _set_power(self, power: int | float | Quantity):
        self._set_power_attr(power)
        self._send_message()

    def _set_power_callback(self, message: RabbitMessage):
        if message.value == "l":
            logger.debug("Reply to set power received.")
        else:
            self.rabbit.send_error("WrongReply", message.to_str())

    def _set_power_attr(self, power: int | float | Quantity):
        if isinstance(power, Quantity):
            def conversion(x: int | float) -> int | float:
                return (self.conversion(x) - power).value

            result = root(conversion, x0=np.array([1]))
            power = round(result.x[0])

        elif isinstance(power, float):
            power = round(float)

        if not (self.power_range[0] < power < self.power_range[1]):
            raise ValueError("Power outside acceptable range.")

        self.power = power

    def _send_message(self):
        # write to pico
        message = RabbitMessage(self.communication, self.name, "write", self._get_message())
        self.rabbit.send(message)

        # get reply
        message = RabbitMessage(self.communication, self.name, "read_until", self._get_message())
        self.rabbit.send(message)
        self._set_reply_alarm(5, self._set_power_callback)

    def _get_message(self) -> str:
        return "l" + str(self.pin).zfill(2) + str(self.frequency).zfill(4) + str(self.power).zfill(3) + "\r"
