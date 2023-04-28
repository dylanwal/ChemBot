import logging

import numpy as np
from scipy.optimize import root
from unitpy import Quantity

from chembot.configuration import config
from equipment.lights.base import Light
from chembot.rabbitmq.messages import RabbitMessageAction, RabbitMessageReply
from chembot.utils.pico_checks import check_GPIO_pins

logger = logging.getLogger(config.root_logger_name + ".lights")


class LightPico(Light):
    """
    LigthPico

    """

    def __init__(self,
                 name: str,
                 communication: str,
                 pin: int,
                 color: Quantity | None = None,
                 frequency: int = 10_000,
                 conversion: callable = None
                 ):
        super().__init__(name)
        self.color = color
        self.communication = communication
        self.pin = pin
        self.frequency = frequency

        self.conversion = conversion
        self.power: int = 0
        self.power_range = (0, 100)
        self.power_quantity: Quantity = Quantity("0 * W/m**2")
        self.power_quantity_range = (self.conversion(0), self.conversion(100))

    def _read_color_message(self, message: RabbitMessageAction):
        self.rabbit.send(RabbitMessageReply(message, self.read_color()))

    def read_color(self) -> Quantity | None:
        """ read_color """
        return self.color

    # def _write_color_message(self, message: RabbitMessageAction):
    #     self.write_color(message.value)
    #     self.rabbit.send(RabbitMessageReply(message, ""))
    #
    # def write_color(self, color: int | Quantity | float | str):
    #     """ write_color """
    #     self.color = color

    def _read_communication_message(self, message: RabbitMessageAction):
        self.rabbit.send(RabbitMessageReply(message, self.read_communication))

    def read_communication(self) -> str:
        """ read_communication """
        return self.communication

    def _write_communication_message(self, message: RabbitMessageAction):
        self.write_communication(message.value)
        self.rabbit.send(RabbitMessageReply(message, ""))

    def write_communication(self, communication: str):
        """
        write_communication

        Parameters
        ----------
        communication:
            communication port (e.g. 'COM9')

        """
        self.communication = communication

    def _read_pin_message(self, message: RabbitMessageAction):
        self.rabbit.send(RabbitMessageReply(message, self.read_pin))

    def read_pin(self) -> int:
        """ read_pin """
        return self.pin

    def _write_pin_message(self, message: RabbitMessageAction):
        self.write_pin(message.value)
        self.rabbit.send(RabbitMessageReply(message, ""))

    def write_pin(self, pin: int):
        """
        write_pin

        Parameters
        ----------
        pin:
            range: [0, 27]

        """
        check_GPIO_pins(pin)
        self.pin = pin

    def _read_frequency_message(self, message: RabbitMessageAction):
        self.rabbit.send(RabbitMessageReply(message, self.read_frequency))

    def read_frequency(self) -> int:
        """ read_frequency """
        return self.frequency

    def _write_frequency_message(self, message: RabbitMessageAction):
        self.write_frequency(message.value)
        self.rabbit.send(RabbitMessageReply(message, ""))

    def write_frequency(self, frequency: int):
        """
        write_frequency

        Parameters
        ----------
        frequency:
            range: [100, 50_000]

        Returns
        -------

        """
        if not isinstance(frequency, int):
            raise TypeError("'frequency' must be an integer.")

        if not (100 < frequency < 50_000):
            raise ValueError("'frequency' must be between [100, 50_000]")

        self.frequency = frequency

    def _write_power_from_message(self, message: RabbitMessageAction):
        self.write_power(message.value)

    def write_power(self, power: int | float | Quantity):
        """
        write_power
        Sets the power setting for
        Parameters
        ----------
        power

        Returns
        -------

        """
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






    def _write_on(self):
        ...

    def _write_off(self):
        ...

    def _activate(self):
        ...

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
