"""
This class is for measuring temperature with a thermocouple and a MAX31855 sensor module.
Temperatures are returned in Celsius.

Wiring:
    MAX31855 VDD to Raspberry Pi 3.3V
    MAX31855 GND to Raspberry Pi GND
    MAX31855 CLK to Raspberry Pi SCLK (GPIO11)
    MAX31855 DO to Raspberry Pi MISO (GPIO9)
    MAX31855 CS to Raspberry Pi CE0 (or any GPIO pin) 'chip select'

    MAX31855 + and - connect to thermocouple (direction matters)



Reference:
    https://learn.adafruit.com/thermocouple/python-circuitpython


"""


import time
import board
import busio
import digitalio
import adafruit_max31855
from time import sleep, time
from math import log1p, pow
from statistics import mean
import matplotlib.pyplot as plt
import numpy as np

class Thermocouple:
    def __init__(self, cs_pin, averaging=False):
        """
        :param cs_pin: this is the chip select pin. It needs to be in format "D#" where the # is the GPIO label
        :param averaging: This employs "exponentially Weighted Moving Averaging" to reduce noise.
        """
        cs = digitalio.DigitalInOut(getattr(board, cs_pin))
        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        self.thermo_probe = adafruit_max31855.MAX31855(spi, cs)
        self.prev_temp = 25
        self.averaging = averaging
        self.get_temp()

    def get_temp(self):
        # Function returns the temperature in Celsius
        temp = self.thermo_probe.temperature
        sleep(0.2)

        # Long term averaging
        if self.averaging:
            # Noise reduction: ‘Exponentially Weighted Moving Average’ (EWMA)
            a = 0.20  # Weighting. Lower value is smoother.
            temp = (1 - a) * self.prev_temp + a * temp

        self.prev_temp = temp
        return round(temp, 2)

##############################################################################################################

# Plotting stuff
def plot():
    # generate initial plot
    plt.axis([0,1,0,1])
    plt.ion()
    plt.show()
    plt.draw()
    plt.pause(0.001)

def plot_update(x, y):
    window_size, num_signals = y.shape

    plt.cla()
    plt.axis([np.min(x),np.max(x),0,100])

    for i in range(num_signals):
        plt.plot(x, y[:,i], '-')

    plt.pause(0.001)

##############################################################################################################
##############################################################################################################

if __name__ == "__main__":
    """
    Mode 1: Print out temperature valves for 1 probe
    Mode 2: Print out temperature valves for n probe
    Mode 3: Print out temperature valves for n probe and plot
    """
    mode = 1

    try:
        if mode == 1:
            print("Reading a single temperature.")
            temperature_tools = Thermocouple("D21")
            sleep(1)
            while True:
                print("temp =" + str(temperature_tools.get_temp()))
                sleep(0.01)

        if mode == 2:
            print("Reading n temperatures.")
            n = 2
            cs_pins = ["D21", "D20"]
            temperature_tools = []
            for i in range(n):
                temperature_tools.append(Thermocouple(cs_pins[i], averaging=True))
            sleep(1)

            # Read temperatures
            temp = [0] * n
            while True:
                for i in range(n):
                    temp[i] = temperature_tools[i].get_temp()

                print("temp =" + str(temp))
                sleep(0.01)

        if mode == 3:
            print("Reading n temperatures and live plotting.")
            n = 2
            cs_pins = ["D21", "D20"]
            temperature_tools = []
            for i in range(n):
                temperature_tools.append(Thermocouple(cs_pins[i], averaging=True))
            sleep(1)

            # Read temperatures
            window_size = 100
            plot()
            temp = np.zeros([1,n])
            temp_data = np.zeros([1,n])
            time_data = np.zeros(1)
            start_time = time()
            ii = 0
            while True:
                for i in range(n):
                    temp[0, i] = temperature_tools[i].get_temp()

                # Add new data
                temp_data = np.append(temp_data, temp, axis=0)
                time_data = np.append(time_data,time()-start_time)

                # remove old data point to keep plot window small
                if ii > window_size:
                    temp_data = temp_data[1:,:]
                    time_data = time_data[1:]
                else:
                    ii += 1

                plot_update(time_data, temp_data)
                print("temp =" + str(temp))
                sleep(0.1)


    finally:
        print("Program Done")
