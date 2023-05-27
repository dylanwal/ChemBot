from serial import Serial, PARITY_EVEN, STOPBITS_ONE
from time import time
port = "COM7"
serial_comm = Serial(port=port, baudrate=115200, parity=PARITY_EVEN, stopbits=STOPBITS_ONE, timeout=0.02)

start = time()
for _ in range(1):
    for i in range(100):
        serial_comm.write("r".encode())
        message = serial_comm.read_until()
        print(f"{i}, {message}")

print(100/(time()-start))

print("done")

# serial.serialutil.SerialException