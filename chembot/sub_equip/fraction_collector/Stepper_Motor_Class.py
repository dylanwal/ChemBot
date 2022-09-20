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


class StepperMotor:
    def __init__(self, pin_step, pin_dir, pin_sleep, step_res='full', end_stop_pin=0, max_rotation=360,
                 Acc_control=False):
        # setup pins
        self.pin_step = pin_step  # define pin
        self.pin_dir = pin_dir  # define pin
        self.pin_sleep = pin_sleep  # define pin
        GPIO.setup(self.pin_step, GPIO.OUT)  # define pin as output
        GPIO.setup(self.pin_dir, GPIO.OUT)  # define pin as output
        GPIO.setup(self.pin_sleep, GPIO.OUT)  # define pin as output
        GPIO.output(self.pin_step, 0)  # initially set pin to 0 or off
        GPIO.output(self.pin_dir, 0)  # initially set pin to 0 or off
        GPIO.output(self.pin_sleep, 0)  # initially set pin to 0 or off

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
        # 350 RPM ~1000Hz or 0.001 s pulse  // 1000 RPM ~3000 Hz or 0.00033 s pulse with full-steps
        self.step_rate = 1 / (self.rot_RPM / 60 * 360) * self.step_angle  # time per step given the RPM and microstep
        self.delay = self.step_rate / 2  # Time between pulses at full speed (sec) * not time of a full pulse
        if self.delay < 0.0003:  # raspberry pi can't pulse faster (good accuracy above 0.001, very bad below 0.0001)
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
        self.total_rotation = 0
        self.rot_dir = 0  # 0 = clockwise, 1 = counter clockwise
        self.max_rotation = max_rotation  # far limit of movement for stepper motor

        # If end_stop_pin is give, it is activated here
        if end_stop_pin != 0:
            self.end_stop_pin = end_stop_pin
            self.end_stop = EndStop(end_stop_pin)

    def rotate(self, degree):
        # wake up driver
        GPIO.output(self.pin_sleep, 1)
        sleep(0.01)  # give time to turn on

        # change stepper rotation direction if needed
        if degree < 0:
            direction = 0
        else:
            direction = 1
        if direction != self.rot_dir:
            self.rot_dir = direction
            GPIO.output(self.pin_dir, direction)
            sleep(0.01)

        # Updating total rotation and check for out of bounce movement
        self.total_rotation = self.total_rotation + degree
        if self.total_rotation > self.max_rotation or self.total_rotation < 0:
            exit('Motor is being asked to move outside the window of [0, max_rotations].')

        # Run Motor
        number_steps = round(abs(degree) / self.step_angle)

        if not self.acc_op:
            # No acceleration control
            for i in range(number_steps):
                GPIO.output(self.pin_step, 1)
                sleep(self.delay)
                GPIO.output(self.pin_step, 0)
                sleep(self.delay)

        else:
            # If acceleration control is enabled, then one of two ramp strategies will be used depending on
            # how large or small the movement is

            if number_steps > self.acceleration_steps * 2:
                # rotate stepper with ramp up and ramp down by percent set by (self.rot_acc)

                full_speed_steps = number_steps - self.acceleration_steps * 2

                # acceleration
                for i in range(self.acceleration_steps):
                    delay = self.delay_slow - (self.delay_slow - self.delay) / self.acceleration_steps * i
                    GPIO.output(self.pin_step, 1)
                    sleep(delay)
                    GPIO.output(self.pin_step, 0)
                    sleep(delay)

                # full speed
                for i in range(full_speed_steps):
                    GPIO.output(self.pin_step, 1)
                    sleep(self.delay)
                    GPIO.output(self.pin_step, 0)
                    sleep(self.delay)

                # de-acceleration
                for i in range(self.acceleration_steps):
                    delay = (self.delay_slow - self.delay) / self.acceleration_steps * i + self.delay
                    GPIO.output(self.pin_step, 1)
                    sleep(delay)
                    GPIO.output(self.pin_step, 0)
                    sleep(delay)

            else:
                # Triangle ramp, for shorter movements
                tri1_steps = round(number_steps / 2)
                tri2_steps = number_steps - tri1_steps
                # acceleration
                for i in range(tri1_steps):
                    delay = self.delay_slow - (self.delay_slow - self.delay) / (5 * 360 / self.step_angle) * i
                    GPIO.output(self.pin_step, 1)
                    sleep(delay)
                    GPIO.output(self.pin_step, 0)
                    sleep(delay)

                # de-acceleration
                for i in range(tri2_steps):
                    delay2 = delay + (self.delay_slow - self.delay) / (5 * 360 / self.step_angle) * i
                    GPIO.output(self.pin_step, 1)
                    sleep(delay2)
                    GPIO.output(self.pin_step, 0)
                    sleep(delay2)

        # Shut down motor driver
        sleep(1)  # give time to have high holding power to prevent inertia from cause extra movement
        GPIO.output(self.pin_sleep, 0)  # put driver to sleep so it doesn't burn up and to save energy

    def zero(self):
        # This code moves motor to end stop
        zero_adj_delay = 1.5  # how much long the delay should be for movement (bigger = slower movement)

        # Check for endstop to be defined
        var = self.end_stop_pin
        check = "var" in locals()
        if not check:
            exit('Endstop pin not given, so zeroing not possibele.')

        # wake up driver
        GPIO.output(self.pin_sleep, 1)
        sleep(0.01)  # give time to turn on

        # Move away from endstop incase it is already there
        # Set direction of movement
        if self.rot_dir != 0:
            self.rot_dir = 0
            GPIO.output(self.pin_dir, self.rot_dir)
            sleep(0.01)

        # Move
        for i in range(400):
            GPIO.output(self.pin_step, 1)
            sleep(self.delay * zero_adj_delay)
            GPIO.output(self.pin_step, 0)
            sleep(self.delay * zero_adj_delay)
        sleep(1)

        # Run Motor till hits end stop or 5 sec
        # change direction of rotation
        self.rot_dir = 1
        GPIO.output(self.pin_dir, self.rot_dir)
        sleep(0.01)

        start_time = time()
        while True:
            if time() - start_time > 5:
                exit("Motor did not hit end stop within 5 sec. Check for issues.")

            if self.end_stop.check_status() == 0:  # Check if hit end stop
                GPIO.output(self.pin_step, 1)
                sleep(self.delay * zero_adj_delay)
                GPIO.output(self.pin_step, 0)
                sleep(self.delay * zero_adj_delay)
            else:
                break

        # Shut down motor driver
        sleep(1)  # give time to have high holding power to prevent inertia from cause extra movement
        GPIO.output(self.pin_sleep, 0)  # put driver to sleep so it doesn't burn up and to save energy


def cleanup():
    # Shut off power to GPIO pins
    GPIO.cleanup()


if __name__ == "__main__":
    example = 2
    try:
        if example == 1:
            # Simple motor turning
            z_axis = StepperMotor(35, 37, 33, step_res='full', max_rotation=360 * 100, Acc_control=True)
            sleep(.1)
            print('spin forward')
            z_axis.rotate(360 * 10)  # 1 full rotation - clockwise
            sleep(.1)  # pause 1 second
            print('spin backwards')
            z_axis.rotate(-360 * 10)  # 1 full rotation - counter clockwise

            sleep(.1)
            print('spin forward')
            z_axis.rotate(360 / 4)  # 1 full rotation - clockwise
            sleep(.1)  # pause 1 second
            print('spin backwards')
            z_axis.rotate(-360 / 4)  # 1 full rotation - counter clockwise

        if example == 2:
            # Zero test
            z_axis = StepperMotor(35, 37, 33, step_res='full', max_rotation=360 * 100, end_stop_pin=31, Acc_control=True)
            sleep(.1)
            print('Moving to zero.')
            z_axis.zero()
            print('Zero reached.')

    finally:
        cleanup()
        print('Program done')
