import enum
import threading

import serial
from serial.tools.list_ports import comports

from chembot import logger, global_ids, configuration
import chembot.communication.base as communication
import errors as errors


class Serial(communication.Communication, serial.Serial):
    # ports that the computer sense there is a device connected
    available_ports = [port.device for port in comports()]
    # ports actively being used
    active_ports = {}

    class ParityOptions(enum.Enum):
        even = serial.PARITY_EVEN
        odd = serial.PARITY_ODD
        none = serial.PARITY_NONE

    def __init__(self,
                 port: str,
                 baud_rate: int = 115200,
                 parity=serial.PARITY_NONE,
                 stop_bits: int = 1,
                 bytes_: int = 8,
                 timeout: float = 0.1,
                 name: str = None
                 ):
        self.id_ = global_ids.get_id(self)

        if port not in self.available_ports:
            # check if port is available
            raise errors.EquipmentError(self, "Port is not connected to computer")

        if port in self.active_ports.keys():
            # check for duplicates
            raise errors.EquipmentError(self, f"CommSerial (id: {self.id_}): Port ({port}) is used by another equipment")

        # process parity options
        if isinstance(parity, Serial.ParityOptions):
            parity = parity.value

        # create new port
        self.serial = serial.Serial.__init__(self, port=port, baudrate=baud_rate, stopbits=stop_bits, bytesize=bytes_,
                                             parity=parity, timeout=timeout)
        self.active_ports[port] = self.serial
        self.flushOutput()
        self.flushInput()

        self.lock = threading.Lock()
        if name is None:
            self.name = f"{type(self).__name__} (id: {self.id_})"

        logger.info(repr(self) + "\n\t\tConnection established.")

    def __repr__(self):
        text = self.name + f" || port: {self.port}, baud rate: {self.baudrate}, byte size= " \
               f"{self.bytesize}, parity = {self.parity}, stop bits = {self.stopbits}, time out = {self.timeout}"
        return text

    def write(self, message: str | bytes, encoding: str = configuration.encoding):
        if not isinstance(message, bytes):
            message = message.encode()
        serial.Serial.write(self, message)
        logger.debug(f"{type(self).__name__} (id: {self.id_}) || Write: " + repr(message))

    def read(self, bytes_: int, decoding: str = configuration.encoding) -> str:
        message = serial.Serial.read(self, bytes_).decode(decoding)
        logger.debug(f"{type(self).__name__} (id: {self.id_}) || Read: " + repr(message))
        return message


if __name__ == '__main__':
    test_serial = Serial('COM5', baud_rate=100)
    test_serial.write(b"110"*500)
