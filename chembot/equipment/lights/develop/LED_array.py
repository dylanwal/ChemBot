"""
This is for quick manual testing of an LED array.

for linux
for sysdevpath in $(find /sys/bus/usb/devices/usb*/ -name dev); do
>     (
>         syspath="${sysdevpath%/dev}"
>         devname="$(udevadm info -q name -p $syspath)"
>         [[ "$devname" == "bus/"* ]] && exit
>         eval "$(udevadm info -q property --export -p $syspath)"
>         [[ -z "$ID_SERIAL" ]] && exit
>         echo "/dev/$devname - $ID_SERIAL"
>     )
> done




"""

from serial import Serial, PARITY_EVEN, STOPBITS_ONE
from serial.tools.list_ports import comports

available_ports = [port.device for port in comports()]  # ports that the computer sense there is a device connected
active_ports = {}  # ports actively being used.


def connect_serial(comm_port, baudrate=115200, parity=PARITY_EVEN, stopbits=STOPBITS_ONE, timeout=0.1):
    if comm_port in active_ports.keys():
        # if serial port already established just hand port back.
        return active_ports[comm_port]
    else:
        if comm_port in available_ports:  # check if port is available
            # create new port
            serial = Serial(port=comm_port, baudrate=baudrate, stopbits=stopbits, parity=parity, timeout=timeout)
            active_ports[comm_port] = serial
            return serial


if __name__ == '__main__':
    test_serial = connect_serial('COM4')
    red_pin = 0
    mint_pin = 1
    green_pin = 2
    cyan_pin = 3
    blue_pin = 4
    violet_pin = 5
    power_pin = 15
    power_pin2 = 14
    freq = 300

    print("\nType 'e1' then 'enter' to exit.")
    mes = "r" + str(power_pin).zfill(2) + "1" + "\r"
    test_serial.write(mes.encode())
    mes = "r" + str(power_pin2).zfill(2) + "1" + "\r"
    test_serial.write(mes.encode())
    print(test_serial.read_until())
    print("")
    print("Enter 'r,m,g,c,b,v' followed by a power level [0, 100]")
    try:
        while True:
            try:
                # get input
                input_string = input()
                color = input_string[0]
                power = int(input_string[1:])
                if 0 <= power <= 100:
                    # do something
                    if color == "r":
                        mes = "l" + str(red_pin).zfill(2) + str(freq).zfill(4) + str(power).zfill(3) + "\r"
                    elif color == "m":
                        mes = "l" + str(mint_pin).zfill(2) + str(freq).zfill(4) + str(power).zfill(3) + "\r"
                    elif color == "g":
                        mes = "l" + str(green_pin).zfill(2) + str(freq).zfill(4) + str(power).zfill(3) + "\r"
                    elif color == "c":
                        mes = "l" + str(cyan_pin).zfill(2) + str(freq).zfill(4) + str(power).zfill(3) + "\r"
                    elif color == "b":
                        mes = "l" + str(blue_pin).zfill(2) + str(freq).zfill(4) + str(power).zfill(3) + "\r"
                    elif color == "v":
                        mes = "l" + str(violet_pin).zfill(2) + str(freq).zfill(4) + str(power).zfill(3) + "\r"
                    elif color == "e":
                        print("exit")
                        break
                    else:
                        print("Invalid color.")
                        continue

                    test_serial.write(mes.encode())
                    print(test_serial.read_until())

                else:
                    print("Power outside valid range.")
            except:
                pass

    finally:
        mes = "e" + "\r"
        test_serial.write(mes.encode())
        print(test_serial.read_until())
        print("lights off, program done")
