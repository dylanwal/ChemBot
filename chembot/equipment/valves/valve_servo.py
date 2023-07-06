import logging

from chembot.configuration import config
from chembot.equipment.valves.valve_configuration import ValveConfiguration, ValvePosition
from chembot.equipment.valves.base_valve import Valve
from chembot.communication.serial_pico import PicoSerial
from chembot.reference_data.pico_pins import PicoHardware
from chembot.rabbitmq.messages import RabbitMessageAction

logger = logging.getLogger(config.root_logger_name + ".valve")


class ValveServo(Valve):
    """
    Servo settings must be set in configuration for each position.
    duty = 400 > value > 2600

    50 Hz (or 20 ms period): This is the most common PWM frequency used for hobbyist servos.
    The pulse width ranges from 1 ms to 2 ms, with 1.5 ms typically representing the center position.
    angles = {
        0: int(65535/20*0.5), 1638 # 65535 bits/ 20 ms * 0.5 = 0.5 ms duty
        90: int(65535/20*1.2), 3932 #
        180: int(65535/20*1.9), 6225 #
        270: int(65535/20*2.5),  8191 # 2.5 ms duty
    }
    """
    def __init__(self,
                 name: str,
                 communication: str,
                 configuration: ValveConfiguration,
                 pin: int,
                 frequency: int = 50
                 ):
        super().__init__(name, configuration)

        self.communication = communication
        self._pin = None
        self.pin = pin
        self._frequency = None
        self.frequency = frequency

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

    def _activate(self):
        # ping communication to ensure it is alive
        message = RabbitMessageAction(self.communication, self.name, "read_name")
        self.rabbit.send_and_consume(message, error_out=True)

        # check that pwm settings set in configuration
        for pos in self.configuration.positions:
            if pos.setting is None:
                raise ValueError("Set servo settings in configuration positions settings.")

        super()._activate()

    def _stop(self):
        pass

    def _move(self, position: ValvePosition):
        message = RabbitMessageAction(
            destination=self.communication,
            source=self.name,
            action=PicoSerial.write_pwm,
            kwargs={"pin": self.pin, "duty": position.setting, "frequency": self.frequency}
        )
        self.rabbit.send(message)

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
        self.pin = pin

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
        self.frequency = frequency

    def _deactivate(self):
        # write to pico
        param = {"pin": self.pin, "value": 0}
        message = RabbitMessageAction(self.communication, self.name, PicoSerial.write_digital, param)
        self.rabbit.send(message)

        # get reply
        self.watchdog.set_watchdog(message, 5)
