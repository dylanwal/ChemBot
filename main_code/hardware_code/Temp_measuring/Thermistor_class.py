"""
This class is for measuring temperature with a thermistor and a MCP3008 Analog to Digital converter.
Temperatures are returned in Celsius.

Wiring:
    MCP3008 VDD to Raspberry Pi 3.3V
    MCP3008 VREF to Raspberry Pi 3.3V
    MCP3008 AGND to Raspberry Pi GND
    MCP3008 DGND to Raspberry Pi GND
    MCP3008 CLK to Raspberry Pi SCLK (GPIO11)
    MCP3008 DOUT to Raspberry Pi MISO (GPIO9)
    MCP3008 DIN to Raspberry Pi MOSI (GPIO10)
    MCP3008 CS/SHDN to Raspberry Pi CE0 (or any GPIO pin) 'chip select'

    MCP3008 CH# should connect the thermistor (with a voltage divider with the same resistor as the thermistor)
    The other end of the the thermistor connect to 3.3V

Reference:
    https://www.paulschow.com/2013/08/monitoring-temperatures-using-raspberry.html
    https://learn.adafruit.com/mcp3008-spi-adc/python-circuitpython

"""


import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
from time import sleep, time
from math import log1p, pow
from statistics import mean
import matplotlib.pyplot as plt
import numpy as np

class Thermistors:
    def __init__(self, cs_pin, position="P0", averaging=False):
        """
        :param cs_pin: this is the chip select pin. It needs to be in format "D#" where the # is the GPIO label
        :param position: This is the position on the mcp3008 you want to read from. It needs to be in format "P#"
        # can range from 0-7
        :param averaging: This employs "exponentially Weighted Moving Averaging" to reduce noise.
        """
        cs = digitalio.DigitalInOut(getattr(board, cs_pin))
        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        mcp = MCP.MCP3008(spi, cs)
        self.chan = AnalogIn(mcp, getattr(MCP, position))
        self.prev_temp = 25
        self.averaging = averaging
        self.get_temp()

    def get_temp(self):
        # Function returns the temperature in Celsius
        n = 10  # number of measurements that are averaged
        volts = []
        for _ in range(n):
            volts.append(self.chan.voltage)
            sleep(0.01)

        # Convert voltage to Celsius
        temp = round(self.volt_to_temp(mean(volts)), 1)

        # Long term averaging
        if self.averaging:
            # Noise reduction: ‘Exponentially Weighted Moving Average’ (EWMA)
            a = 0.20  # Weighting. Lower value is smoother.
            temp = (1 - a) * self.prev_temp + a * temp

        self.prev_temp = temp
        return round(temp, 2)

    @staticmethod
    def volt_to_temp(volts):
        if volts == 0:
            return 0
        ohms = ((1 / volts) * 3300) - 1000  # calculate the ohms of the thermististor
        lnohm = log1p(ohms)  # take ln(ohms)

        # a, b, & c values from http://www.thermistor.com/calculators.php
        # using curve R (-6.2%/C @ 25C) Mil Ratio X
        a = 0.002197222470870
        b = 0.000161097632222
        c = 0.000000125008328

        # Steinhart Hart Equation
        # T = 1/(a + b[ln(ohm)] + c[ln(ohm)]^3)
        t1 = (b * lnohm)  # b[ln(ohm)]
        c2 = c * lnohm  # c[ln(ohm)]
        t2 = pow(c2, 3)  # c[ln(ohm)]^3
        temp = 1 / (a + t1 + t2)  # calculate temperature

        temp_c = temp - 273.15 - 4  # K to C
        # the -4 is error correction for bad python math
        return temp_c


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
    mode = 3

    try:
        if mode == 1:
            print("Reading a single temperature. Position 0.")
            temperature_tools = Thermistors("D8", "P0")
            sleep(1)
            while True:
                print("temp =" + str(temperature_tools.get_temp()))
                sleep(0.01)

        if mode == 2:
            print("Reading n temperatures.")
            n = 2
            positions_used = ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"]
            temperature_tools = []
            for i in range(n):
                temperature_tools.append(Thermistors("D8", position=positions_used[i], averaging=True))
            sleep(1)

            # Read temperatures
            temp = [0] * n
            while True:
                for i in range(n):
                    temp[i] = temperature_tools[i].get_temp()

                print("temp =" + str(temp))
                sleep(0.1)

        if mode == 3:
            print("Reading n temperatures and live plotting.")
            n = 2
            positions_used = ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"]
            temperature_tools = []
            for i in range(n):
                temperature_tools.append(Thermistors("D8", position=positions_used[i], averaging=True))
            sleep(1)


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
