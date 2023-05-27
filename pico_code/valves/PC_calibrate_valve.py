"""
Calibrate servo test

To control servo position, the duty is changed.
for 180 degree servo, this range is 1-2 microseconds
for 270 degree servo, this range is 0.5-2.5 microseconds
both servos use 50 Hz signal or (20 ms)

the pico pwm duty is defined by 16 bits (0 to 65535)


"""
import time

import serial


def main():
    s = serial.Serial(port="COM3", parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE, timeout=5)
    print(s.read_all().decode())
    s.flushOutput()
    s.flushInput()

    angles = {
        0: int(65535/20*0.5),  # 65535 bits/ 20 ms * 0.5 = 0.5 ms duty
        90: int(65535/20*1.2),  #
        180: int(65535/20*1.9),  #
        270: int(65535/20*2.5),  # 2.5 ms duty
    }
    pin = 0
    frequency = 50

    for angle, duty in angles.items():
        s.write(f"p{pin:02}{duty:05}{frequency:09}\n".encode())  # s001
        mes = s.read_until()
        print(angle, mes.decode().strip("\n"))
        time.sleep(2)

    s.write("r\n".encode())
    s.read_until()
    print('done')


if __name__ == "__main__":
    main()
