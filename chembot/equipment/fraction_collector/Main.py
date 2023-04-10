# This code is the main code for the operation of the fraction collector.
# This coded requires connection to a PC where it will receive instructions.
# IMPORTANT: PC code must be started first!


import socket
import Position_Class
import Stepper_Motor_Class


mess_format = 'utf-8'


class SocketFractionCollector:
    def __init__(self):
        print('Trying to connect to PC...')
        self.TCP_IP = '192.168.0.2'  # PC host IP address
        self.TCP_PORT = 5005
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.TCP_IP, self.TCP_PORT))
        print('Connection achieved.')
        self.buffer_size = 1024

    def receive_instructions(self, FC):
        # Listen for messages
        msg = self.s.recv(self.buffer_size)

        # Decode message
        msg = msg.decode(mess_format)
        msg = msg.split(",")
        msg_type = msg[0]
        msg_data = msg[1]

        # Types of reference_data accepted and running FC code
        if msg_type == "Layout":
            FC.layout = msg_data
            print("Test tube rack layout is: ", FC.layout)
        elif msg_type == "Zero":
            FC.zero()
            print("All axis have been zeroed.")
            print("Tube Position: A1")
        elif msg_type == "Tube":
            print("Tube Position: " + msg_data)
            FC.move(msg_data)
        elif msg_type == "End":
            self.disconnect()
            return "break"
        else:
            msg = "Wrong message type received from main computer"
            self.s.send(bytes(msg, mess_format))
            exit(msg)

        # Send confirmation
        self.s.send(bytes("OK", mess_format))

    def disconnect(self):
        self.s.close()


if __name__ == '__main__':
    # Start connection
    connection = SocketFractionCollector()
    # Setup fraction collector
    FC = Position_Class()  # Position_Class.FractionCollector(plot=True, motor=False)
    out = "Error check"
    try:
        while True:
            # continuously listen for input
            return_exit = connection.receive_instructions(FC)
            if return_exit == "break":
                out = "OK"
                print("Program done with no errors.")
                break

    finally:
        if out != "OK":
            print("Unexpected error occurred.")
        Stepper_Motor_Class.cleanup()
