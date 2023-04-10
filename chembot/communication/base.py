import logging
import abc

from chembot.configuration import config
from chembot.rabbitmq.rabbitmq_core import RabbitEquipment, RabbitMessage

logger = logging.getLogger(config.root_logger_name + ".communication")


class Communication(RabbitEquipment):

    def __init__(self, name: str):
        super().__init__(name)
        self.name = name

    def action_write(self, message: RabbitMessage):
        logger.debug(f"{self.name} || Write: " + repr(message.value))
        self._write(message.value)

        if "reply_action" in message.parameters:
            message.action = message.parameters["reply_action"]
            self.action_read(message)

    def action_read(self, message: RabbitMessage):
        if "read_bytes" in message.parameters:
            read_bytes = int(message.parameters["read_bytes"])
        else:
            read_bytes = 1

        reply = self._read(read_bytes)
        logger.debug(f"{self.name} || read: " + repr(message))

        message = RabbitMessage(message.source, message.destination, "reply", reply)
        self.rabbit.send(message)

    def action_read_until(self, message: RabbitMessage):
        if "symbol" in message.parameters:
            symbol = message.parameters["symbol"]
        else:
            symbol = '\n'

        reply = self._read_until(symbol)
        logger.debug(f"{self.name} || read_until: " + repr(message))

        message = RabbitMessage(message.source, message.destination, "reply", reply)
        self.rabbit.send(message)

    @abc.abstractmethod
    def action_flush_buffer(self):
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
