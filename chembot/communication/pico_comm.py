import logging

import serial
from serial.tools.list_ports import comports

from chembot.configuration import config
from chembot.communication.communication import Communication
from chembot.rabbitmq.messages import RabbitMessageAction, RabbitMessageReply
from chembot.utils.pico_pins import PicoHardware

logger = logging.getLogger(config.root_logger_name + ".communication")


def encode_message(text: str):
    return text.replace("\n", "__n__").replace("\r", "__r__")


def decode_message(text: str):
    return text.replace("__n__", "\n").replace("__r__", "\r")


def validate_digital_resistor(resistor: str) -> str:
    if resistor is None:
        return "n"
    else:
        if resistor in ("u", "d"):
            return resistor

    raise ValueError("Invalid resistor option for pico digital.")


class PicoSerial(Communication):
    """
    Pico serial

    """
    available_ports = [port.device for port in comports()]

    def __init__(self,
                 name: str,
                 port: str,
                 ):
        super().__init__(name)

        if port not in self.available_ports:
            raise ValueError(f"Port '{port}' is not connected to computer.")
        self.serial = serial.Serial(port=port, parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE, timeout=10)

    def __repr__(self):
        return self.name + f" || port: {self.port}"

    def _read_port_message(self, message: RabbitMessageAction):
        self.rabbit.send(RabbitMessageReply(message, self.read_port()))

    def read_port(self) -> str:
        """ read_port """
        return self.port

    def _activate(self):
        self._write_flush_buffer()

    def _deactivate(self):
        self.serial.close()

    def _write_write(self, message: str):
        message = encode_message(message) + "\n"
        self.serial.write(message.encode(config.encoding))

    def _read_read(self, read_bytes: int) -> str:
        message = self.serial.read(read_bytes).decode(config.encoding)
        return decode_message(message.strip("\n"))

    def write_write_read_until(self, message: str, symbol: str = "\n") -> str:
        self.write_write(message)
        return self.read_read_until(symbol)

    def _read_read_until(self, symbol: str = "\n") -> str:
        return self.serial.read_until(symbol.encode(config.encoding)).decode(config.encoding)

    def _write_flush_buffer(self):
        self.serial.flushInput()
        self.serial.flushOutput()

    def write_digital(self, pin: int, value: int, resistor: str = None):
        """
        write digital
        Turn GPIO pin on or off

        Parameters
        ----------
        pin: int
            GPIO pin
        value: int
            0: off; 1 on
            range: [0, 1]
        resistor:
            'n': No resistor, 'u': pull up, 'd': pull down
            range: ['n', 'u', 'd']

        """
        PicoHardware.validate_GPIO_pin(pin)
        resistor = validate_digital_resistor(resistor)
        if value not in (0, 1):
            raise ValueError(f"Digital value can only be [0, 1]. \ngiven: {value}")

        reply = self.write_write_read_until(f"d{pin:02}o{resistor}{value}")

        if reply is not "d":
            raise ValueError(f"Unexpected reply from Pico.\n reply:{reply}")

    def read_digital(self, pin: int, resistor: str = None) -> int:
        """
        read_digital

        Parameters
        ----------
        pin: int
            GPIO pin
        resistor:
            'n': No resistor, 'u': pull up, 'd': pull down
            range: ['n', 'u', 'd']

        """
        PicoHardware.validate_GPIO_pin(pin)
        resistor = validate_digital_resistor(resistor)

        reply = self.write_write_read_until(f"d{pin:02}i{resistor}")

        if reply[0] != "d":
            raise ValueError(f"Unexpected reply from Pico.\n reply:{reply}")

        return int(reply[1])

    def read_analog(self, pin: int) -> int:
        """
        read_analog

        Parameters
        ----------
        pin: int
            GPIO pin
            range: [0, 1, 2, 3, 4]

        Returns
        -------
        value: int
            range: [0, ..., 65535]
        """
        PicoHardware.validate_adc_pin(pin)

        reply = self.write_write_read_until(f"a{pin:02}")

        if reply[0] != "a":
            raise ValueError(f"Unexpected reply from Pico.\n reply:{reply}")

        return int(reply[1])

    def write_pwm(self, pin: int, duty: int, freq: int):
        PicoHardware.validate_GPIO_pin(pin)
        if not (0 < duty < 65535):
            raise ValueError(f"pwm duty must be between [0, 65535].\n given:{duty}")

        reply = self.write_write_read_until(f"p{pin:02}o{resistor}{value}")

        if reply is not "p":
            raise ValueError(f"Unexpected reply from Pico.\n reply:f{reply}")