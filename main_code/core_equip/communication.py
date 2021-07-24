"""



"""

from serial import Serial, PARITY_EVEN, STOPBITS_ONE
from serial.tools.list_ports import comports


available_ports = [port.device for port in comports()]  # ports that the computer sense there is a device connected
active_ports = {}  # ports actively being used.


def connect_serial(comm_port, baudrate=115200, parity=PARITY_EVEN, stopbits=STOPBITS_ONE, timeout=0.1):
    if comm_port in active_ports.keys():
        # if serial port already established just hand port back. 
        return active_ports[comm_port]
    else:
        if comm_port in available_ports:  # check if port is available
            # create new port
            serial = Serial(port=comm_port, baudrate=baudrate, stopbits=stopbits, parity=parity, timeout=timeout)
            active_ports[comm_port] = serial
            return serial


if __name__ == '__main__':
    test_serial = connect_serial('COM4')
    test_serial2 = connect_serial('COM9')
    print(test_serial)
