# This code is to test the fraction collector code operation.
# This code is to be run on the PC as the server.
# Several modes are available
# Mode 1: Zero all axis
# Mode 2: Zero all axis + User input tube
# Mode 3: Zero all axis + {automatic} Move through all tube positions
# Mode 4: Zero all axis + {automatic} Long term repeatability test

import socket
from string import ascii_uppercase
from time import sleep


mess_format = 'utf-8'


class SeverComm:
    def __init__(self):
        print('Starting server')
        self.TCP_IP = socket.gethostbyname(socket.gethostname())
        self.TCP_PORT = 5005
        print('Server IP address: ', self.TCP_IP, '  Server Port: ', self.TCP_PORT)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('Listening for connections...')
        self.s.bind((self.TCP_IP, self.TCP_PORT))
        self.s.listen(1)
        client_connection, client_address = self.s.accept()
        self.conn = client_connection
        print('Connection achieved with: ', client_address)
        self.buffer_size = 1024   # max size of messages to be sent

    def send_data(self, data_type, data_out="None"):  # First entry is reference_data type, second entry is reference_data
        if len(data_out) < self.buffer_size-20:
            if isinstance(data_out, str):
                msg = data_type + ',' + data_out
                self.conn.send(bytes(msg, mess_format))
        else:
            exit("The reference_data that is being sent is to long. Adjust message or buffer(both in client and server)")

        # wait for confirmation
        confirmation = self.conn.recv(self.buffer_size)
        if "OK" != confirmation.decode(mess_format):
            exit("Error message received:" + confirmation.decode(mess_format))

    def disconnect(self):
        self.conn.send(bytes("End" + "," + "End", mess_format))
        self.s.close()


if __name__ == '__main__':     # Program starts from here
    # Parameters
    FC_layout = '23ml_test_tubes'
    mode = 1

    # Starting Connection
    FC_connection = SeverComm()

    # Send tray layout and zero
    FC_connection.send_data("Layout", FC_layout)  # First entry is reference_data type, second entry is reference_data

    try:
        if mode == 1:
            # Zero all axis
            print('Sending zero all axis command.')
            FC_connection.send_data("Zero")
            print('All axis have been zeroed.')

        elif mode == 2:
            # Zero all axis
            print('Sending zero all axis command.')
            FC_connection.send_data("Zero")
            print('All axis have been zeroed.')

            # endless loop asking user for vial position
            print("To End the program enter 'end'. ")
            while True:
                vial = input("Please enter tube (format: A1, B2, etc.):")
                # Break out of loop and end program
                if vial == 'end':
                    break
                # Send and receive reference_data from Pi
                FC_connection.send_data("Tube", vial)

        elif mode == 3:
            # Zero all axis
            print('Sending zero all axis command.')
            FC_connection.send_data("Zero")
            print('All axis have been zeroed.')

            # Define all tube spots
            if FC_layout == '23ml_test_tubes':
                LETTERS = list(ascii_uppercase[:12])
                NUMBERS = list(map(str, list(range(1, 16))))  # 15 spots but last number in range not included so 16
                print(LETTERS)
                print(NUMBERS)

            # Loop through all tube positions in order
            print("To End the program enter 'end'. ")
            for letter in LETTERS:
                for num in NUMBERS:
                    vial = letter + num
                    print("Moving to position to:" + vial)
                    # Send and receive reference_data from Pi
                    FC_connection.send_data("Tube", vial)

        elif mode == 4:
            # Zero all axis
            print('Sending zero all axis command.')
            FC_connection.send_data("Zero")
            print('All axis have been zeroed.')

            # move back and fourth between two positions repeatedly
            cycles = 10
            for i in range(cycles):
                FC_connection.send_data("Tube", "D3")
                print("Moving to position to:" + "D3")
                sleep(5)
                FC_connection.send_data("Tube", "J13")
                print("Moving to position to:" + "J13")
                print("Cycle " + str(i+1) + " out of " + str(cycles))
                sleep(5)

        else:
            exit("Not a valid mode.")

    # closing out the program and breaking connection
    finally:
         FC_connection.disconnect()
         print('Program done!')
