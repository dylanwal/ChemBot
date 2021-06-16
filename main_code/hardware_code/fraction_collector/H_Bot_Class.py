# This module drives the A4988 stepper motor driver with Kysan 1124090 Nema 17 Stepper Motor
# A4988: https://www.pololu.com/product/1182
# Stepper Motor: https://ultimachine.com/products/kysan-1124090-nema-17-stepper-motor
#    Holding Torque:  5.5Kg.cm, NO.of Phase:  2, Step Angle:  1.8° ± 5%, Resistance Per Phase:  2.8Ω± 10%,
#    Inductance Per Phase:  4.8mH± 20%,
#    Current Per Phase:  1.5A, Shaft:  5mm diameter w/ one flat

from time import sleep, time
import RPi.GPIO as GPIO
from End_Stop_Class import EndStop

GPIO.setmode(GPIO.BOARD)  # use numbers 1-40


class HBot:
    def __init__(self, pin_step, pin_dir, pin_sleep, pin_step2, pin_dir2, pin_sleep2, step_res='full',
                 end_stop_pin_x=32, end_stop_pin_y=38, Acc_control=False):
        # Motor 1 setup pins
        self.pin_step = pin_step  # define pin
        self.pin_dir = pin_dir  # define pin
        self.pin_sleep = pin_sleep  # define pin
        GPIO.setup(self.pin_step, GPIO.OUT)  # define pin as output
        GPIO.setup(self.pin_dir, GPIO.OUT)  # define pin as output
        GPIO.setup(self.pin_sleep, GPIO.OUT)  # define pin as output
        GPIO.output(self.pin_step, 0)  # initial set pin to 0 or off
        GPIO.output(self.pin_dir, 0)  # initial set pin to 0 or off
        GPIO.output(self.pin_sleep, 0)  # initial set pin to 0 or off

        # Motor 2 setup pins
        self.pin_step2 = pin_step2  # define pin
        self.pin_dir2 = pin_dir2  # define pin
        self.pin_sleep2 = pin_sleep2  # define pin
        GPIO.setup(self.pin_step2, GPIO.OUT)  # define pin as output
        GPIO.setup(self.pin_dir2, GPIO.OUT)  # define pin as output
        GPIO.setup(self.pin_sleep2, GPIO.OUT)  # define pin as output
        GPIO.output(self.pin_step2, 0)  # initial set pin to 0 or off
        GPIO.output(self.pin_dir2, 0)  # initial set pin to 0 or off
        GPIO.output(self.pin_sleep2, 0)  # initial set pin to 0 or off

        # setup motor stepping
        self.step_res = step_res  # options: full, half, quarter, eighth, sixteenth !!!!! change wiring to match  !!!!!
        self.full_step_angle = 1.8  # degrees; from motor specifications
        if self.step_res == 'full':
            self.step_angle = self.full_step_angle
        elif self.step_res == 'half':
            self.step_angle = self.full_step_angle / 2
        elif self.step_res == 'quarter':
            self.step_angle = self.full_step_angle / 4
        elif self.step_res == 'eighth':
            self.step_angle = self.full_step_angle / 8
        elif self.step_res == 'sixteenth':
            self.step_angle = self.full_step_angle / 16
        else:
            exit('invalid stepper resolution')

        # Motor Speed
        self.rot_RPM = 400  # 350 typical use RPM, determined from torque curve (can be increased up to 1000)
        self.step_rate = 1 / (self.rot_RPM / 60 * 360) * self.step_angle  # time per step given the RPM and microstep
        self.delay = self.step_rate / 2  # Time between pulses at full speed (sec) * not time of a full pulse
        if self.delay < 0.0003:  # raspberry pi can't pulse faster than this
            print(self.delay)
            self.delay = 0.0003
            print('RPM too high, and automatically lowered')
        # Acceleration
        self.acc_op = Acc_control
        self.rot_RPM_slow = 20  # start RPM
        self.step_rate_slow = 1 / (self.rot_RPM_slow / 60 * 360) * self.step_angle
        self.delay_slow = self.step_rate_slow / 2
        self.acceleration_steps = 30

        # Current motor position
        self.rot_dir1 = 0  # 0 = clockwise, 1 = counter clockwise
        self.rot_dir2 = 0  # 0 = clockwise, 1 = counter clockwise

        # End stop
        self.end_stop_x = EndStop(end_stop_pin_x)
        self.end_stop_y = EndStop(end_stop_pin_y)

    def rotate(self, rot_1, rot_2):  # rot in degrees
        # wake up driver
        GPIO.output(self.pin_sleep, 1)
        GPIO.output(self.pin_sleep2, 1)
        sleep(0.01)  # give time to turn on

        # change stepper rotation direction if needed
        if rot_1 < 0:
            direction1 = 0
        else:
            direction1 = 1
        if rot_2 < 0:
            direction2 = 0
        else:
            direction2 = 1

        if direction1 != self.rot_dir1:
            self.rot_dir1 = direction1
            GPIO.output(self.pin_dir, direction1)
            sleep(0.01)
        if direction2 != self.rot_dir2:
            self.rot_dir2 = direction2
            GPIO.output(self.pin_dir2, direction2)
            sleep(0.01)

        # Run Motor
        number_steps1 = round(rot_1 / self.step_angle)
        number_steps2 = round(rot_2 / self.step_angle)

        if not self.acc_op:
            # No acceleration control
            if number_steps1 > number_steps2:
                # Case 1: Motor 1 has to do more rotations
                number_steps = number_steps1
                for i in range(number_steps):
                    if i < number_steps2:
                        GPIO.output(self.pin_step, 1)
                        GPIO.output(self.pin_step2, 1)
                        sleep(self.delay)
                        GPIO.output(self.pin_step, 0)
                        GPIO.output(self.pin_step2, 0)
                        sleep(self.delay)
                    else:
                        GPIO.output(self.pin_step, 1)
                        sleep(self.delay)
                        GPIO.output(self.pin_step, 0)
                        sleep(self.delay)
            else:
                # Case 2: Motor 2 has to do more rotations
                number_steps = number_steps2
                for i in range(number_steps):
                    if i < number_steps1:
                        GPIO.output(self.pin_step, 1)
                        GPIO.output(self.pin_step2, 1)
                        sleep(self.delay)
                        GPIO.output(self.pin_step, 0)
                        GPIO.output(self.pin_step2, 0)
                        sleep(self.delay)
                    else:
                        GPIO.output(self.pin_step2, 1)
                        sleep(self.delay)
                        GPIO.output(self.pin_step2, 0)
                        sleep(self.delay)

        else:
            pass  # this can be added if acceleration control needed

        # Shut down motor driver
        sleep(1)  # give time to have high holding power to prevent inertia from cause extra movement
        GPIO.output(self.pin_sleep, 0)  # put driver to sleep so it doesn't burn up and to save energy
        GPIO.output(self.pin_sleep2, 0)  # put driver to sleep so it doesn't burn up and to save energy

    def zero(self):
        # This code moves motor to end stop
        zero_adj_delay = 1.5  # how much long the delay should be for movement (bigger = slower movement)

        # wake up driver
        GPIO.output(self.pin_sleep, 1)
        GPIO.output(self.pin_sleep2, 1)
        sleep(0.01)  # give time to turn on

        # Move away from endstop incase it is already there
        # Set direction of movement
        if self.rot_dir1 != 0:
            self.rot_dir1 = 0
            GPIO.output(self.pin_dir, self.rot_dir1)
            sleep(0.01)

        # Move
        for i in range(400):
            GPIO.output(self.pin_step, 1)
            sleep(self.delay * zero_adj_delay * zero_adj_delay)
            GPIO.output(self.pin_step, 0)
            sleep(self.delay * zero_adj_delay * zero_adj_delay)
        sleep(1)


        # X end stop
        # define direction
        if self.rot_dir1 != 0:
            self.rot_dir1 = 0
            GPIO.output(self.pin_dir, self.rot_dir1)
        if self.rot_dir2 != 0:
            self.rot_dir2 = 0
            GPIO.output(self.pin_dir2, self.rot_dir2)
        sleep(0.01)

        # Run Motor till hits end stop or 5 sec
        start_time = time()
        while True:
            if time()-start_time > 5:
                exit("Motor did not hit 'x' end stop within 5 sec. Check for issues.")

            if self.end_stop_x.check_status() == 0:
                GPIO.output(self.pin_step, 1)
                GPIO.output(self.pin_step2, 1)
                sleep(self.delay * zero_adj_delay)
                GPIO.output(self.pin_step, 0)
                GPIO.output(self.pin_step2, 0)
                sleep(self.delay * zero_adj_delay)
            else:
                break

        # Y end stop
        # define direction
        if self.rot_dir1 != 1:
            self.rot_dir1 = 1
            GPIO.output(self.pin_dir, self.rot_dir1)
        if self.rot_dir2 != 0:
            self.rot_dir2 = 0
            GPIO.output(self.pin_dir2, self.rot_dir2)
        sleep(0.01)

        # Run Motor till hits end stop or 5 sec
        start_time = time()
        while True:
            if time()-start_time > 5:
                exit("Motor did not hit 'x' end stop within 5 sec. Check for issues.")

            if self.end_stop_y.check_status() == 0:
                GPIO.output(self.pin_step, 1)
                GPIO.output(self.pin_step2, 1)
                sleep(self.delay * zero_adj_delay)
                GPIO.output(self.pin_step, 0)
                GPIO.output(self.pin_step2, 0)
                sleep(self.delay * zero_adj_delay)
            else:
                break

        # Shut down motor driver
        sleep(1)  # give time to have high holding power to prevent inertia from cause extra movement
        GPIO.output(self.pin_sleep, 0)  # put driver to sleep so it doesn't burn up and to save energy
        GPIO.output(self.pin_sleep2, 0)


def cleanup():
    # Shut off power to GPIO pins
    GPIO.cleanup()


if __name__ == "__main__":
    example = 2
    try:
        if example == 1:
            # Simple motor turning
            xy_axis = HBot(37, 35, 40, 31, 29, 33, step_res='full', end_stop_pin_x=32, end_stop_pin_y=38)
            sleep(.1)
            print('Moving')
            xy_axis.rotate(-360 * 5, 0)
            xy_axis.rotate(-360 * 5, -360 * 5)
            xy_axis.rotate(360 * 5, -360 * 5)
            sleep(1)
            xy_axis.rotate(360 * 5, 0)
            xy_axis.rotate(360 * 5, 360 * 5)
            xy_axis.rotate(+360 * 5, 360 * 5)
            print('moving done')

        if example == 2:
            # Zero test
            xy_axis = HBot(37, 35, 40, 31, 29, 33, step_res='full', end_stop_pin_x=32, end_stop_pin_y=38)
            sleep(.1)
            print('Moving to zero.')
            xy_axis.zero()
            print('Zero reached.')

    finally:
        cleanup()
        print('Program done')
