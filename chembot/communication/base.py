import logging
import abc

from chembot.configuration import config
from chembot.equipment.equipment import Equipment
from chembot.rabbitmq.message import RabbitMessage

logger = logging.getLogger(config.root_logger_name + ".communication")


class Communication(Equipment):
    """ Base Communication """
    def __init__(self, name: str):
        super().__init__(name)

    def _activate(self):
        pass

    def _deactivate(self):
        pass

    def action_write(self, message: RabbitMessage):
        self._write(message.value)
        logger.debug(config.log_formatter(type(self).__name__, self.name, f"Write: " + repr(message.value)))

    def action_read(self, message: RabbitMessage):
        if "read_bytes" in message.parameters:
            read_bytes = int(message.parameters["read_bytes"])
        else:
            read_bytes = 1

        reply = self._read(read_bytes)
        logger.debug(config.log_formatter(type(self).__name__, self.name, f"Read: " + repr(message)))

        message = RabbitMessage(message.source, message.destination, "reply", reply)
        self.rabbit.send(message)

    def action_read_until(self, message: RabbitMessage):
        if "symbol" in message.parameters:
            symbol = message.parameters["symbol"]
        else:
            symbol = '\n'

        reply = self._read_until(symbol)
        logger.debug(config.log_formatter(type(self).__name__, self.name, f"Read_until: " + repr(message)))

        message = RabbitMessage(message.source, message.destination, "reply", reply)
        self.rabbit.send(message)

    @abc.abstractmethod
    def action_flush_buffer(self, message: RabbitMessage):
        ...

    @abc.abstractmethod
    def _write(self, message: str):
        ...

    @abc.abstractmethod
    def _read(self, bytes_: int) -> str:
        ...

    @abc.abstractmethod
    def _read_until(self, symbol: str = "\n") -> str:
        ...
