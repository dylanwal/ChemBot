"""

For port: check Device Manager/Ports, USB Serial Port


# Wiring:
          FT232R    Pico
        * RX        TX (GPIO_0, UART0)
        * TX        RX (GPIO_1, UART0)
        * GND       GND
        * VCC       (don't connect, can kill Pico if 5 V)
        * DTR/RTS   Any GPIO (GPIO_2)    RTS: Request to send (1:no request, 0: request - not sure)
        * CTS       (not used currently)  CTS: Clear to send (1: ready, 0: not ready - not sure)

Trouble_shooting hint: if no message is being received try switching RX and TX connections.

"""

from time import sleep

from serial import Serial, STOPBITS_TWO, PARITY_EVEN, PARITY_NONE, STOPBITS_ONE


def phase_sensor():
    port = "COM6"
    serial_comm = Serial(port=port, baudrate=19200, parity=PARITY_EVEN, stopbits=STOPBITS_ONE, timeout=1)

    state = "standby"
    while state == "standby":
        serial_comm.write("run\n".encode())
        message = serial_comm.read_until().decode().replace("\n", "")
        if message == "run":
            state = "run"
        print(f"trying to connect {port}")
        sleep(1)

    for _ in range(10):
        print(serial_comm.read_until())

    serial_comm.write("stop".encode())


if __name__ == '__main__':
    phase_sensor()

