import logging
import abc

from chembot.configuration import config
from chembot.equipment.equipment import Equipment
from chembot.rabbitmq.messages import RabbitMessageAction, RabbitMessageReply

logger = logging.getLogger(config.root_logger_name + ".communication")


class Communication(Equipment, abc.ABC):
    """ Base Communication """

    def _write_write_message(self, message: RabbitMessageAction):
        self.write_write(message.value)
        self.rabbit.send(RabbitMessageReply(message, ""))

    def write_write(self, message: str):
        """
        write_write

        Parameters
        ----------
        message: str
            message to write

        """
        self._write_write(message)
        logger.debug(config.log_formatter(self, self.name, f"Action | write: " + repr(message)))

    def _read_read_message(self, message: RabbitMessageAction):
        result = self.read_read(message.value)
        self.rabbit.send(RabbitMessageReply(message, result))

    def read_read(self, read_bytes: int = 1) -> str:
        """
        read_read

        Parameters
        ----------
        read_bytes: int
            number of bytes to read

        Returns
        -------
        results: str

        """
        reply = self._read_read(read_bytes)
        logger.debug(config.log_formatter(self, self.name, f"Action | read: " + repr(reply)))
        return reply

    def _read_read_until_flush(self, message: RabbitMessageAction):
        result = self.read_read(message.value)
        self.rabbit.send(RabbitMessageReply(message, result))

    def read_read_until(self, symbol: str = '\n') -> str:
        """
        read_read_until

        Parameters
        ----------
        symbol: str
            symbol that signifies end of message

        Returns
        -------
        results: str

        """
        reply = self._read_read_until(symbol)
        logger.debug(config.log_formatter(self, self.name, f"Action | read_until: " + repr(reply)))
        return reply.strip("\n").strip("\r")

    def _write_flush_buffer_message(self, message: RabbitMessageAction):
        self.write_flush_buffer()
        self.rabbit.send(RabbitMessageReply(message, ""))

    def write_flush_buffer(self):
        """ write_flush_buffer """
        self._write_flush_buffer()

    @abc.abstractmethod
    def _write_flush_buffer(self):
        ...

    @abc.abstractmethod
    def _write_write(self, message: str):
        ...

    @abc.abstractmethod
    def _read_read(self, bytes_: int) -> str:
        ...

    @abc.abstractmethod
    def _read_read_until(self, symbol: str = "\n") -> str:
        ...
