import enum
import logging

import serial
from serial.tools.list_ports import comports

from chembot.configuration import config
from chembot.communication.base import Communication

logger = logging.getLogger(config.root_logger_name + ".communication" + ".mock")


class ParityOptions(enum.Enum):
    EVEN = serial.PARITY_EVEN
    ODD = serial.PARITY_ODD
    NONE = serial.PARITY_NONE


class MockComm(Communication):
    available_ports = [port.device for port in comports()]

    def __init__(self,
                 name: str,
                 **kwargs
                 ):
        super().__init__(name)

    def __repr__(self):
        return self.name + f" || port: {self.port}"

    def _write(self, message: str):
        logger.debug(f"{self.name} || write: " + repr(message))

    def _read(self, read_bytes: int) -> str:
        return "mock read"

    def _read_until(self, symbol: str = "\n") -> str:
        return "mock read_until"

    def action_flush_buffer(self):
        logger.debug("buffer flush")

    def activate(self):
        super().activate()

    def _get_details(self) -> dict:
        return {
            "name": self.name,
            "port": self.port
        }

    def action_deactivate(self):
        logger.debug("MOCK: deactivate")
        super().action_deactivate()
