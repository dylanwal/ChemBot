from serial import Serial, PARITY_EVEN, STOPBITS_ONE
from time import time
port = "COM3"
serial_comm = Serial(port=port, baudrate=57600, parity=PARITY_EVEN, stopbits=STOPBITS_ONE, timeout=0.1)
start = time()
for _ in range(1):
    for i in range(1000):
        serial_comm.write("r".encode())
        message = serial_comm.read_until()
        # print(f"{i}, {message}")

print(1000/(time()-start))

print("done")

