import enum
import logging

import serial
from serial.tools.list_ports import comports

from chembot.configuration import config
from chembot.communication.base import Communication
from chembot.rabbitmq.message import RabbitMessage

logger = logging.getLogger(config.root_logger_name + "comm")


class ParityOptions(enum.Enum):
    EVEN = serial.PARITY_EVEN
    ODD = serial.PARITY_ODD
    NONE = serial.PARITY_NONE


class Serial(Communication):
    available_ports = [port.device for port in comports()]

    def __init__(self,
                 name: str,
                 port: str,
                 baud_rate: int = 115200,
                 parity: ParityOptions = ParityOptions.NONE,
                 stop_bits: int = 1,
                 bytes_: int = 8,
                 timeout: float = 0.1,
                 ):
        super().__init__(name)

        if port not in self.available_ports:
            # check if port is available
            raise ValueError(f"Port '{port}' is not connected to computer.")
        # create new port
        self.serial = serial.Serial.__init__(self, port=port, baudrate=baud_rate, stopbits=stop_bits, bytesize=bytes_,
                                             parity=parity, timeout=timeout)

    def __repr__(self):
        return self.name + f" || port: {self.port}"

    def set_baud_rate(self, message: RabbitMessage):
        self.serial.baudrate = message.value

    def _activate(self):
        self.serial.flushOutput()
        self.serial.flushInput()

    def _get_details(self) -> dict:
        return {
            "name": self.name,
            "port": self.port
        }

    def _deactivate(self):
        self.serial.close()

    def _write(self, message: str):
        self.serial.write(message.encode(config.encoding))

    def _read(self, read_bytes: int) -> str:
        return self.serial.read(read_bytes).decode(config.encoding)

    def _read_until(self, symbol: str = "\n") -> str:
        return self.serial.read_until(symbol.encode(config.encoding)).decode(config.encoding)

    def action_flush_buffer(self, message: RabbitMessage):
        self.serial.flushInput()
        self.serial.flushOutput()
