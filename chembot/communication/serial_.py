import logging
import time

import serial
from serial.tools.list_ports import comports

from chembot.configuration import config
from chembot.communication.communication import Communication

logger = logging.getLogger(config.root_logger_name + ".communication")


class Serial(Communication):
    available_ports = [port.device for port in comports()]

    def __init__(self,
                 name: str,
                 port: str,
                 baud_rate: int = 9600,
                 parity: str = 'N',
                 stop_bits: int = 1,
                 bytes_: int = 8,
                 timeout: float = 10,
                 ):
        super().__init__(name)

        if port not in self.available_ports:
            raise ValueError(f"Port '{port}' is not connected to computer.")
        self.serial = serial.Serial(port=port, baudrate=baud_rate, stopbits=stop_bits, bytesize=bytes_,
                                    parity=parity, timeout=timeout)
        self.port = port
        self.baud_rate = baud_rate
        self.stop_bits = stop_bits
        self.bytes_ = bytes_
        self.parity = parity
        self.timeout = timeout

        self.attrs += ['port', "baud_rate", "stop_bits", "bytes_", "parity", "timeout"]

    def __repr__(self):
        return self.name + f" || port: {self.serial.port}"

    def _activate(self):
        self._write_flush_buffer()

    def _deactivate(self):
        self.serial.close()

    def _write_flush_buffer(self):
        self.serial.flushInput()
        self.serial.flushOutput()

    def _write(self, message: str):
        self.serial.write(message.encode(config.encoding))

    def _read(self, read_bytes: int) -> str:
        return self.serial.read(read_bytes).decode(config.encoding)

    def _read_until(self, symbol: str = "\n") -> str:
        return self.serial.read_until(symbol.encode(config.encoding)).decode(config.encoding)

    def read_port(self) -> str:
        """ read_port """
        return self.serial.port

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

    def read_baudrate(self) -> str:
        """ read_baudrate """
        return self.serial.baudrate

    def read_buffer_in(self) -> int:
        """ read number of bytes in the 'in' buffer """
        return self.serial.in_waiting

    def read_buffer_out(self) -> int:
        """ read number of bytes in the 'in' buffer """
        return self.serial.out_waiting

    def read_all_buffer(self) -> str:
        """ read all data in buffer """
        return self.read(self.serial.in_waiting)

    def write_plus_read_all_buffer(self, message: str, delay: float = 0.2) -> str:
        """ write then read all buffer """
        self.write(message)
        time.sleep(delay)  # give time for replay
        return self.read_all_buffer()
