"""
Calibrate servo test
"""
import machine
import time


def main():
    pwm = machine.PWM(machine.Pin(15))
    pwm.freq(50)

    angles = [
        [0, int(65535/20*0.5)],  # 65535 bits/ 20 ms * 0.5 = 0.5 ms duty
        [90, int(65535/20*1.2)],  #
        [180, int(65535/20*1.9)],  #
        [270, int(65535/20*2.5)],  # 2.5 ms duty
    ]

    for angle in angles:
        pwm.duty_u16(angle[1])
        time.sleep(1)

    pwm.deinit()
    off = machine.Pin(15, machine.Pin.OUT)
    off.value(0)


if __name__ == '__main__':
    main()
