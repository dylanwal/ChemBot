import enum

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
                 timeout=0.1
                 ):
        self.id_ = global_ids.get_id(self)

        if port not in self.available_ports:
            # check if port is available
            raise errors.EquipmentError(self, "Port is not connected to computer")

        if port in self.active_ports.keys():
            # check for duplicates
            raise errors.EquipmentError(self, f"CommSerial (id: {self.id_}): Port ({port}) is used by another equipment")

        # create new port
        self.serial = serial.Serial.__init__(self, port=port, baudrate=baud_rate, stopbits=stop_bits,
                                             parity=parity, timeout=timeout)
        self.active_ports[port] = self.serial
        self.flushOutput()
        self.flushInput()

        logger.info(repr(self) + "\n\t\tConnection established.")

    def __repr__(self):
        text = f"{type(self).__name__} (id: {self.id_}) || port: {self.port}, baud rate: {self.baudrate}, byte size= " \
               f"{self.bytesize}, parity = {self.parity}, stop bits = {self.stopbits}, time out = {self.timeout}"
        return text

    def write(self, message: str, encoding: str = configuration.encoding):
        serial.Serial.write(self, message.encode())
        logger.debug(f"{type(self).__name__} (id: {self.id_}) || Write: " + message)

    def read(self, bytes_: int, decoding: str = configuration.encoding) -> str:
        message = serial.Serial.read(self, bytes_).decode(decoding)
        logger.debug(f"{type(self).__name__} (id: {self.id_}) || Read: " + str(message))
        return message


if __name__ == '__main__':
    test_serial = Serial('COM5')
    test_serial.write("fish")
