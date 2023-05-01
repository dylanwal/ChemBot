import enum
import logging

import serial
from serial.tools.list_ports import comports

from chembot.configuration import config
from chembot.communication.communication import Communication
from chembot.rabbitmq.messages import RabbitMessage

logger = logging.getLogger(config.root_logger_name + ".communication" + ".mock")


class ParityOptions(enum.Enum):
    EVEN = serial.PARITY_EVEN
    ODD = serial.PARITY_ODD
    NONE = serial.PARITY_NONE


class MockComm(Communication):
    """ MockComm """

    available_ports = [port.device for port in comports()]

    def __init__(self,
                 name: str,
                 **kwargs
                 ):
        super().__init__(name)

    def __repr__(self):
        return self.name + f" || port: {self.port}"

    def _write(self, message: str):
        logger.debug(config.log_formatter(type(self).__name__, self.name, "MOCK write: " + repr(message)))

    def _read(self, read_bytes: int) -> str:
        return "MOCK read"

    def _read_until(self, symbol: str = "\n") -> str:
        return "MOCK read_until"

    def action_flush_buffer(self, message: RabbitMessage):
        logger.debug("buffer flush")

    def _get_details(self) -> dict:
        return {
            "name": self.name,
            "port": self.port
        }
