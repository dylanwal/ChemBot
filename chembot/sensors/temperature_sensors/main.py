# This code is the main code for the operation of the fraction collector.
# This coded requires connection to a PC where it will receive instructions.
# IMPORTANT: PC code must be started first!

import threading
import concurrent.futures
import queue
import socket
import Temp_PID_Heating


mess_format = 'utf-8'


class SocketTempHeating:
    def __init__(self, queue, event):
        print('Trying to connect to PC...')
        self.TCP_IP = '192.168.0.2'  # PC host IP address
        self.TCP_PORT = 5005
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.TCP_IP, self.TCP_PORT))
        print('Connection achieved.')
        self.buffer_size = 1024
        self.queue = queue
        self.event = event

    def receive_instructions(self):
        # Listen for messages
        msg = self.s.recv(self.buffer_size)

        # Decode message
        msg = msg.decode(mess_format)
        msg = msg.split(",")
        msg_type = msg[0]
        msg_data = msg[1]

        # Types of reference_data accepted and running FC code
        if msg_type == "layout":
            print("Temperature system layout: " + msg_data)
            self.queue.put(msg_data)
        elif msg_type == "temp_set":
            print("New temperature_sensors set: " + msg_data)
            self.queue.put(float(msg_data))
        elif msg_type == "End":
            self.disconnect()
            event.set()
            return
        else:
            msg = "Wrong message type received from main computer"
            self.s.send(bytes(msg, mess_format))
            exit(msg)

        # Send confirmation
        self.s.send(bytes("OK", mess_format))

    def disconnect(self):
        self.s.close()


def listening_thread(queue, event):
    # Start connection
    connection = SocketTempHeating(queue, event)
    while not event.is_set():  # continuously listen for input
        connection.receive_instructions()

    print("Communication Thread Closed")


if __name__ == '__main__':
    show_temp_op = True
    record_data = True
    try:
        pipeline = queue.Queue(maxsize=3)
        event = threading.Event()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            listening_thread = executor.submit(listening_thread, pipeline, event)  # Launch communication thread
            heater_thread = executor.submit(Temp_PID_Heating.heating_temp_thread, pipeline, event, show_temp_op, record_data)  # Launch PID thread
            listening_thread.result()
            heater_thread.result()

    finally:
        print("Program Done")