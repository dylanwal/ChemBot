"""This code covers everything"""

import board
import pulseio
import Thermistor_class
import Thermocouple_class
from time import sleep, time
import numpy as np
import PID
import threading
import concurrent.futures
import queue
import pandas as pd


class PID_Heater:
    def __init__(self, queue, event, layout="layout_1", show_temp_op=False, record_data=False):
        self.queue = queue
        self.event = event

        print(layout)
        print(len(layout))

        if layout == "layout_1":
            heat_pad_pin, temp_probe, PID_K, PID_D, PID_I, temp_probe, temperature_tools, max_temp = layout_1(
                "heating_pad")
        else:
            exit("Wrong layout")

        # Temperature probes
        self.record_data = record_data
        self.show_temp = show_temp_op
        self.temp_tools = temperature_tools
        self.temp_probe = temp_probe
        self.current_temp = self.get_all_temp()

        # PID controller
        self.setpoint = 25  # temp in c
        self.update_freq = 1 / 1  # Hz
        self.PID_controler = PID.PID(PID_K, PID_D, PID_I, sample_time=1 / self.update_freq, setpoint=self.setpoint)
        self.PID_controler.output_limits = (0, 1)

        # Heater:
        self.current_heat_duty = 0
        self.max_temp = max_temp
        self.heater = pulseio.PWMOut(getattr(board, heat_pad_pin), duty_cycle=self.current_heat_duty, frequency=60)

    def run(self):
        error_timer = time()
        if self.record_data:
            start_time = time()
            record_time = np.zeros(1)
            record_setpoint = np.zeros(1)
            record_duty = np.zeros(1)
            record_temp = np.zeros((1, len(self.temp_tools)))

        while not self.event.is_set():
            # check for new set point
            if not self.queue.empty():
                self.setpoint = self.queue.get()
                self.PID_controler.update_setpoint(self.setpoint)
                if self.setpoint > self.max_temp:
                    exit("set point temperature_sensors set too high")

            # measure all temperatures
            self.current_temp = self.get_all_temp()

            # check for issues
            if any(temp < 18 or temp > self.max_temp for temp in self.current_temp):
                print("temp error" + str(self.max_temp))
                if time() - error_timer > 10:
                    error_timer = time()
                elif time() - error_timer > 5:
                    print(self.max_temp)
                    self.heater.duty_cycle = 0
                    self.event.set()
                    exit("max temperature_sensors hit or thermocouple signal lost")
            else:
                # update PID and heater
                self.current_heat_duty = round(self.PID_controler(self.current_temp[self.temp_probe]), 3)
                self.heater.duty_cycle = int(65535 * self.current_heat_duty)  # 16 bit PDW generator

            if self.show_temp:
                print(
                    f"Set temp.: {self.setpoint} oC   Heat[0,1]: {self.current_heat_duty} Temp.: {self.current_temp} oC")

            if self.record_data:
                record_time = np.append(record_time, time() - start_time)
                record_setpoint = np.append(record_setpoint, self.setpoint)
                record_duty = np.append(record_duty, self.current_heat_duty)
                record_temp = np.vstack((record_temp, np.array(self.current_temp)))

            sleep(1 / self.update_freq)

        if self.record_data:
            df = pd.DataFrame({"time": record_time, "set point": record_setpoint, "duty": record_duty})
            for i in range(len(self.temp_tools)):
                col_names = "temp" + str(i)
                df.insert(3 + i, col_names, record_temp[:, i], True)

            print(df.head())
            df.to_csv("/home/pi/Desktop/Thermo_control/PID_data.csv", index=False)

        self.cleanup()

    def get_all_temp(self):
        temp = []
        for probe in self.temp_tools:
            temp.append(probe.get_temp())

        return temp

    def get_one_temp(self, probe_num):
        return self.temp_tools[probe_num].get_temp()

    def cleanup(self):
        self.heater.duty_cycle = 0
        print("setting heater to zero")


def layout_1(options):
    # Temperature probes
    temperature_tools = [Thermistor_class.Thermistors("D8", "P0", averaging=True),
                         Thermistor_class.Thermistors("D8", "P1", averaging=True),
                         Thermocouple_class.Thermocouple("D21", averaging=True),
                         Thermocouple_class.Thermocouple("D20", averaging=True)]

    # PID parameters
    temp_probe = 0  # the temperature_sensors probe for PID control
    PID_K = 0.00001
    PID_D = 500
    PID_I = 1
    heat_pad_pin = "D18"
    max_temp = 100

    if options is "temp_probes":
        return temperature_tools
    elif options is "heating_pad":
        return heat_pad_pin, temp_probe, PID_K, PID_D, PID_I, temp_probe, temperature_tools, max_temp
    else:
        exit()


def heating_temp_thread(queue, event, show_temp_op=False, record_data=False):
    # wait for layout information before starting up PID
    layout = queue.get()
    # Start PID control
    heating_temp = PID_Heater(queue, event, layout=layout, show_temp_op=show_temp_op, record_data=record_data)
    heating_temp.run()

    print("Heating thread done")


def main_input(queue, event):
    queue.put("layout_1")
    print('type *end* to stop program')
    while not event.is_set():
        temp = input("Please enter temp:")
        # Break out of loop and end program
        if temp == 'end':
            event.set()
            break
        try:
            queue.put(float(temp))
        except:
            print('invalid input')
            pass

    print("Input thread closed")


##############################################################################################################
##############################################################################################################


# Run Code (plotting only right now)
if __name__ == '__main__':
    """
    Mode 1: Runs PID controller, set temperature_sensors can be changed on the fly, reference_data will be saved to csv

    """
    mode = 1

    try:
        if mode == 1:
            show_temp_op = True
            record_data = True

            pipeline = queue.Queue(maxsize=3)
            event = threading.Event()
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                input_thread = executor.submit(main_input, pipeline, event)
                pid_thread = executor.submit(heating_temp_thread, pipeline, event, show_temp_op, record_data)
                input_thread.result()  # print out any errors
                pid_thread.result()  # print out any errors

    finally:
        print("End of code!")