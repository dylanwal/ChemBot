import logging

from unitpy import Quantity

from chembot.reference_data.pico_pins import PicoHardware
from chembot.configuration import config
from chembot.equipment.lights.light import Light
from chembot.rabbitmq.messages import RabbitMessageAction
from chembot.communication.serial_pico import PicoSerial

logger = logging.getLogger(config.root_logger_name + ".lights")


class LightPico(Light):
    """
    Light Pico

    """

    def __init__(self,
                 name: str,
                 communication: str,
                 pin: int,
                 color: Quantity | None = None,
                 frequency: int = 10_000,
                 ):
        super().__init__(name)
        self.color = color
        self.communication = communication
        self._pin = None
        self.pin = pin
        self._frequency = None
        self.frequency = frequency

        self.power: int = 0
        self.attrs += ["color", "communication", "pin", "frequency"]
        self.update += ["power"]

    @property
    def pin(self) -> int:
        return self._pin

    @pin.setter
    def pin(self, pin: int):
        PicoHardware.validate_GPIO_pin(pin)
        self._pin = pin
        
    @property
    def frequency(self) -> int:
        return self._frequency

    @frequency.setter
    def frequency(self, frequency: int):
        PicoHardware.validate_pwm_frequency(frequency)
        if not isinstance(frequency, int):
            raise TypeError("'frequency' must be an integer.")
        if not (100 < frequency < 50_000):
            raise ValueError("'frequency' must be between [100, 50_000]")
        self._frequency = frequency

    def _write_on(self):
        self.write_power(65535)

    def _write_off(self):
        self.write_power(0)

    def _activate(self):
        # ping communication to ensure it is alive
        message = RabbitMessageAction(self.communication, self.name, "read_name")
        self.rabbit.send_and_consume(message, error_out=True)
        super()._activate()

    def _stop(self):
        self._write_off()

    def read_color(self) -> Quantity:
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
            range: [0:1:27]

        """
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
            range: [100:1:50_000]

        Returns
        -------

        """
        self.frequency = frequency

    def write_power(self, power: int):
        """
        Sets the power setting for

        Parameters
        ----------
        power:
            light intensity
            range: [0:1:65535]
        """
        if power > 0:
            self.state = self.states.RUNNING
        elif power == 0:
            self.state = self.states.STANDBY

        self.power = power

        # write to pico
        if self.power == 65535:
            param = {"pin": self.pin, "value": 1}
            message = RabbitMessageAction(self.communication, self.name, PicoSerial.write_digital, param)
        elif self.power == 0:
            param = {"pin": self.pin, "value": 0}
            message = RabbitMessageAction(self.communication, self.name, PicoSerial.write_digital, param)
        else:
            param = {"pin": self.pin, "duty": self.power, "frequency": self.frequency}
            message = RabbitMessageAction(self.communication, self.name, PicoSerial.write_pwm, param)

        self.rabbit.send(message)

    def _deactivate(self):
        # write to pico
        param = {"pin": self.pin, "value": 0}
        message = RabbitMessageAction(self.communication, self.name, PicoSerial.write_digital, param)
        self.rabbit.send(message)

        # get reply
        self.watchdog.set_watchdog(message, 5)
