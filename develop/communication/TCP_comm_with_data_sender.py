# send data

import socket
import json
import time

mess_format = 'utf-8'

class intialize_comm:
    def __init__(self, *data_labels):
        print('Waiting for connection from PC...')
        self.TCP_IP = '192.168.0.11'
        self.TCP_PORT = 5005
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((self.TCP_IP, self.TCP_PORT))
        self.s.listen(1)
        conn, addr = self.s.accept()
        self.conn = conn
        print('Connection achived with: ', addr)
#         if data_labels is not None:
#             self.send_labels(data_labels)
        if data_labels is ():
            self.buffer_size = 1024
        stop_comm = 'stop_comm'
        self.stop_comm = stop_comm.encode(mess_format)


    def send_labels(self, data_labels):
        # sending data labels
        self.num_data_points = len(data_labels)
        self.buffer_size = len(json.dumps(data_labels).encode(mess_format))
        self.conn.sendall(str(self.buffer_size).encode(mess_format))
        self.conn.sendall(json.dumps(data_labels).encode(mess_format))
        self.buffer_size = self.num_data_points*10 # 4+ each number*sig.fig

    def send(self,data):
        data_out = ','.join(str(i) for i in data)
        self.conn.sendall(data_out.encode(mess_format))
        return

    def recieve(self):
        data_in = self.conn.recv(self.buffer_size)
        data_in = data_in.decode(mess_format)
        data_in = [float(s) for s in data_in.split(',')]
        #print(data_in)
        return data_in

    def disconnect(self):
        self.s.close()



if __name__ == '__main__':
## This allows to control the car with the keyboard
## Needs to be run with PC code: comm_PC_side.py

    import sys
    # custum written support files
    sys.path.insert(1, '/home/pi/Documents/Projects/Self_drive_car/Support_codes/')
    import motor_control_v1 as motor_control
    import Main_run_code_support_v1 as Main_run_code_support

    data_out = [0, 0]
    motors = motor_control.Motor_Control()
    connection = intialize_comm()

    try:
        while True:
            connection.send(data_out)
            data_in = connection.recieve()
            print(data_in)
            motors.motor_update(data_in[0],data_in[1])

    except ValueError:
        Main_run_code_support.close_out(motors)
        print('Program done!')

    except:
        Main_run_code_support.close_out(motors)
        print('Unexpected error occured')