import serial
from time import sleep
from datetime import datetime, timedelta

with serial.Serial('COM3', baudrate=115200, timeout=10) as ser:
    totalDiff = timedelta(seconds=0.0)

    for i in range(10):
        startTime = datetime.now()
        ser.write(b'b')
        answer = ser.readline()
        endTime = datetime.now()
        answer = answer.strip()
        print(answer)
        totalDiff += endTime - startTime

    print(f"Average rt time: {totalDiff / 100.0}")


import time
import os
import serial


with serial.Serial('COM3', baudrate=115200, timeout=0.01) as ser:
    while True:
        time.sleep(0.01)
        command = "hi" + "\n"
        ser.write(bytes(command.encode('ascii')))
        if ser.inWaiting() > 0:
            pico_data = ser.readline()
            pico_data = pico_data.decode("utf-8", "ignore")
            print(pico_data)


import time
import serial
import serial.tools.list_ports

def check_for_port(port):
    ports = serial.tools.list_ports.comports()
    for port_ in ports:
        if port_.name == port:
            return True
    return False


port = 'COM3'
serial_connected = 0
if check_for_port(port):
    ser_port = serial.Serial(port=port, baudrate=115200)
    print(f"Port open: {ser_port.is_open}")

    while True:
        size = ser_port.inWaiting()
        if size:
            data = ser_port.read(size)
            print(data.decode("utf-8", "ignore"))
        else:
            print('nope')
        time.sleep(1)

else:
    print(f"No port {port} detected.")
