from serial import Serial, PARITY_EVEN, STOPBITS_ONE
from serial.tools.list_ports import comports

import chembot.core_equip.communication as communication
import errors as errors


class CommSerial(communication.Communication, Serial):
    # ports that the computer sense there is a device connected
    available_ports = [port.device for port in comports()]
    # ports actively being used
    active_ports = {}

    def __init__(self, comm_port: str, baudrate: int = 115200, parity=PARITY_EVEN, stopbits=STOPBITS_ONE, timeout=0.1):
        if comm_port in self.active_ports.keys():
            raise errors.CommunicationError("Port is already being used.")

        if comm_port not in self.available_ports:  # check if port is available
            raise errors.CommunicationError("Port is not connected to computer")

        # create new port
        self.serial = Serial.__init__(self, port=comm_port, baudrate=baudrate, stopbits=stopbits, parity=parity,
                                      timeout=timeout)
        self.active_ports[comm_port] = self.serial
        self.comm_port = comm_port
        self.flushOutput()
        self.flushInput()


if __name__ == '__main__':
    test_serial = CommSerial('COM4')
    print(test_serial)
