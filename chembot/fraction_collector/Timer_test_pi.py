# test speed of timer

from time import sleep, time
from math import exp
import matplotlib.pyplot as plt
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)  # use numbers 1-40
GPIO.setup(40, GPIO.OUT)  # define pin as output
GPIO.output(40, 0)

n = 75
delay_time = [0] * n
delay = [0] * n

for i in range(n):
    delay_time[i] = exp(-(i+75)/15)
    start = time()
    for ii in range(50):
        GPIO.output(40, 1)
        sleep(delay_time[i]/2)
        GPIO.output(40, 0)
        sleep(delay_time[i]/2)
    delay[i] = (time() - start)/50

plt.plot(delay_time, delay)
plt.plot([0.0001, 2], [0.0001, 2], '--')
plt.xscale('log')
plt.yscale('log')
plt.xlabel("set timer")
plt.ylabel("actual value")
plt.show()