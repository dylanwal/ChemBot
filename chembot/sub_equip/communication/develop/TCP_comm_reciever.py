# recieve data

import socket
import json
import numpy as np
import time

mess_format = 'utf-8'


class intialize_comm:
    def __init__(self):
        print('Trying to connect to PI...')
        self.TCP_IP = '192.168.0.11'
        self.TCP_PORT = 5005
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.TCP_IP, self.TCP_PORT))
        self.buffer_size = 1024
        print('Connected to PI.')

    def receive_data_labels(self):
        # Receiving data labels
        self.buffer_size = 64
        mess_length = self.s.recv(self.buffer_size)
        data_labels = self.s.recv(int(mess_length.decode(mess_format)))
        self.data_labels = json.loads(data_labels.decode(mess_format))
        self.num_data_points = len(self.data_labels)
        self.buffer_size = self.num_data_points*10
        print(self.data_labels)

    def receive_data(self):
        data_in = self.s.recv(self.buffer_size)
        data_in = data_in.decode(mess_format)
        data_in = np.fromstring(data_in, dtype=float, sep=',')
        #print(data_in)
        return data_in

    def send_data(self, data_out=None):
        if data_out is None:
            data_out = [0, 0]

        data_out = ','.join(str(i) for i in data_out)
        self.s.sendall(data_out.encode(mess_format))
        return

    def disconnect(self):
        self.s.close()


if __name__ == '__main__':     # Program starts from here
    import keyboard
    connection = intialize_comm()
    motor_data = [0.2, 0.2]  # speed, angle

    try:
        while True:
            connection.receive_data()
            if keyboard.is_pressed(' '):
                print('Data collection ended.')
                break

            # motor inputs
            if keyboard.is_pressed('up'):
                if motor_data[0] < 1:
                    motor_data[0] = motor_data[0] + 0.1
                if motor_data[0] > 1:
                    motor_data[0] = 1
            elif keyboard.is_pressed('down'):
                if motor_data[0] > -1:
                    motor_data[0] = motor_data[0] - 0.1
                if motor_data[0] < -1:
                    motor_data[0] = -1
            else:
                if motor_data[0] >= 0.1:
                    motor_data[0] = motor_data[0] - 0.05
                elif motor_data[0] <= -0.1:
                    motor_data[0] = motor_data[0] + 0.05
                else:
                    motor_data[0] = 0

            if keyboard.is_pressed('right'):
                if motor_data[1] < 90:
                    motor_data[1] = motor_data[1] + 10
                if motor_data[1] > 90:
                    motor_data[1] = 90
            elif keyboard.is_pressed('left'):
                if motor_data[1] > -90:
                    motor_data[1] = motor_data[1] - 10
                if motor_data[1] < -90:
                    motor_data[1] = -90
            else:
                if motor_data[1] >= 10:
                    motor_data[1] = motor_data[1] - 5
                elif motor_data[1] <= -10:
                    motor_data[1] = motor_data[1] + 5
                else:
                    motor_data[1] = 0

            motor_data = [round(i, 2) for i in motor_data]
            connection.send_data(data_out=motor_data)
            #time.sleep(0.1)

    finally:
        connection.disconnect()
        print('program done!')
