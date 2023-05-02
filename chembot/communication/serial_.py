import logging

import serial
from serial.tools.list_ports import comports

from chembot.configuration import config
from chembot.communication.communication import Communication
from chembot.rabbitmq.messages import RabbitMessageAction, RabbitMessageReply

logger = logging.getLogger(config.root_logger_name + ".communication")


class Serial(Communication):
    available_ports = [port.device for port in comports()]

    def __init__(self,
                 name: str,
                 port: str,
                 baud_rate: int = 115200,
                 parity: str = 'N',
                 stop_bits: int = 1,
                 bytes_: int = 8,
                 timeout: float = 10,
                 ):
        super().__init__(name)

        if port not in self.available_ports:
            raise ValueError(f"Port '{port}' is not connected to computer.")
        self.serial = serial.Serial(self, port=port, baudrate=baud_rate, stopbits=stop_bits, bytesize=bytes_,
                                             parity=parity, timeout=timeout)

    def __repr__(self):
        return self.name + f" || port: {self.port}"

    def _read_port_message(self, message: RabbitMessageAction):
        self.rabbit.send(RabbitMessageReply(message, self.read_port()))

    def read_port(self) -> str:
        """ read_port """
        return self.port

    def _read_parity_message(self, message: RabbitMessageAction):
        self.rabbit.send(RabbitMessageReply(message, self.read_parity()))

    def read_parity(self) -> str:
        """
        read_parity
        PARITY_NONE, PARITY_EVEN, PARITY_ODD, PARITY_MARK, PARITY_SPACE = 'N', 'E', 'O', 'M', 'S'

        Returns
        -------
        parity:
            parity
            range: ['N', 'E', 'O', 'M', 'S']

        """
        return self.serial.parity

    def _read_stop_bits_message(self, message: RabbitMessageAction):
        self.rabbit.send(RabbitMessageReply(message, self.read_stop_bits()))

    def read_stop_bits(self) -> int:
        """
        read_stop_bits
        STOPBITS_ONE, STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO = (1, 1.5, 2)

        Returns
        -------
        stop_bits:
            stop_bits
            range: [1, 1.5, 2]

        """
        return self.serial.stopbits

    def _read_bytes_message(self, message: RabbitMessageAction):
        self.rabbit.send(RabbitMessageReply(message, self.read_stop_bits()))

    def read_bytes(self) -> int:
        """
        read_bytes

        Returns
        -------
        bytes:
            bytes
            range: [7, 8, 9]

        """
        return self.serial.bytesize

    def _read_baudrate(self, message: RabbitMessageAction):
        self.rabbit.send(RabbitMessageReply(message, self.read_baudrate()))

    def read_baudrate(self) -> str:
        """ read_baudrate """
        return self.serial.baudrate

    def _activate(self):
        self._write_flush_buffer()

    def _deactivate(self):
        self.serial.close()

    def _write_write(self, message: str):
        self.serial.write(message.encode(config.encoding))

    def _read_read(self, read_bytes: int) -> str:
        return self.serial.read(read_bytes).decode(config.encoding)

    def _read_read_until(self, symbol: str = "\n") -> str:
        return self.serial.read_until(symbol.encode(config.encoding)).decode(config.encoding)

    def _write_flush_buffer(self):
        self.serial.flushInput()
        self.serial.flushOutput()
