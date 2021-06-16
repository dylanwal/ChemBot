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


from serial import Serial, STOPBITS_TWO, PARITY_EVEN, PARITY_NONE, STOPBITS_ONE



if __name__ == '__main__':
    port = "COM6"
    serial_comm = Serial(port=port, baudrate=19200, parity=PARITY_EVEN, stopbits=STOPBITS_ONE, timeout=5, rtscts=True)
    #serial_comm.write("hi".encode())
    for _ in range(100):
        print(serial_comm.read_until())
