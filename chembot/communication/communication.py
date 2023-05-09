import logging
import abc

from chembot.configuration import config
from chembot.equipment.equipment import Equipment

logger = logging.getLogger(config.root_logger_name + ".communication")


class Communication(Equipment, abc.ABC):
    """ Base Communication """

    def write(self, message: str):
        """
        write_write

        Parameters
        ----------
        message: str
            message to write

        """
        self._write(message)
        logger.debug(config.log_formatter(self, self.name, f"Action | write: " + repr(message)))

    def read(self, read_bytes: int = 1) -> str:
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
        reply = self._read(read_bytes)
        logger.debug(config.log_formatter(self, self.name, f"Action | read: " + repr(reply)))
        return reply

    def read_until(self, symbol: str = '\n') -> str:
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
        reply = self._read_until(symbol)
        logger.debug(config.log_formatter(self, self.name, f"Action | read_until: " + repr(reply)))
        return reply.strip("\n").strip("\r")

    def write_flush_buffer(self):
        """ write_flush_buffer """
        self._write_flush_buffer()

    def write_plus_read_until(self, message: str, symbol: str = "\n") -> str:
        self.write_write(message)
        return self.read_read_until(symbol)

    @abc.abstractmethod
    def _write_flush_buffer(self):
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
