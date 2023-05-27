# This module checks the status of the end stop
# Returns 1 if it is pushed or 0 if it is not

from time import sleep
import RPi.GPIO as GPIO


GPIO.setmode(GPIO.BOARD)  # use numbers 1-40


class EndStop:
    def __init__(self, pin):
        self.pin = pin   # define pin
        GPIO.setup(self.pin, GPIO.IN)  # define pin as input

    def check_status(self):
        return GPIO.input(self.pin)


def cleanup():
    # Shut off power to GPIO pins
    GPIO.cleanup()


if __name__ == "__main__":
    try:
        end_stop = EndStop(36)
        sleep(0.5)

        for i in range(25):
            print(end_stop.check_status())  # Return 1 for pushed, 0 for not pushed
            sleep(0.2)

    finally:
        cleanup()
        print('Program done')
