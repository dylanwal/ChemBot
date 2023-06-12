import logging

from unitpy import Quantity

from chembot.reference_data.pico_pins import PicoHardware
from chembot.configuration import config
from chembot.equipment.equipment import NotDefinedAttribute
from chembot.equipment.lights.light import Light
from chembot.rabbitmq.messages import RabbitMessageAction

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
                 ):
        super().__init__(name)
        self.color = color if color is not None else NotDefinedAttribute()
        self.communication = communication
        self.pin = pin
        self.frequency = frequency

        self.power: int = 0
        self.attrs += ["color", "communication", "pin", "frequency"]
        self.update += ["power"]

    def _write_on(self):
        self.write_power(65535)

    def _write_off(self):
        self.write_power(0)

    def _activate(self):
        # ping communication to ensure it is alive
        message = RabbitMessageAction(self.communication, self.name, "read_name")
        self.rabbit.send(message)
        self.watchdog.set_watchdog(message, 5)

    def read_color(self) -> Quantity | NotDefinedAttribute:
        """ read_color """
        return self.color

    def read_communication(self) -> str:
        """ read_communication """
        return self.communication

    def write_communication(self, communication: str):
        """
        write_communication

        Parameters
        ----------
        communication:
            communication port (e.g. 'COM9')

        """
        self.communication = communication

    def read_pin(self) -> int:
        """ read_pin """
        return self.pin

    def write_pin(self, pin: int):
        """
        write_pin

        Parameters
        ----------
        pin:
            range: [0, 27]

        """
        PicoHardware.validate_GPIO_pin(pin)
        self.pin = pin

    def read_frequency(self) -> int:
        """ read_frequency """
        return self.frequency

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

    def write_power(self, power: int):
        """
        Sets the power setting for

        Parameters
        ----------
        power:
            light intensity
            range: [0, ..., 65535]
        """
        if power > 0:
            self.state = self.equipment_config.states.RUNNING
        elif power == 0:
            self.state = self.equipment_config.states.STANDBY

        self.power = power

        # write to pico
        param = {"pin": self.pin, "duty": self.power, "frequency": self.frequency}
        message = RabbitMessageAction(self.communication, self.name, "write_pwm", param)
        self.rabbit.send(message)

        # get reply
        self.watchdog.set_watchdog(message, 1)

    def _deactivate(self):
        # write to pico
        param = {"pin": self.pin, "duty": 0, "frequency": self.frequency}
        message = RabbitMessageAction(self.communication, self.name, "write_pwm", param)
        self.rabbit.send(message)

        # get reply
        self.watchdog.set_watchdog(message, 5)
