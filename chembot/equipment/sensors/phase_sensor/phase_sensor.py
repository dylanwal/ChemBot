"""
Phase Sensor Class

For details on the phase sensor see:
* pico_code/phase_sensor/PICO_phase_sensor_PIO_USB.py


A single phase sensor typically consists of 8 detectors which can constantly stream reference_data over a serial port.
It is expected that a single serial port only has one phase sensor associated with it to maximize reference_data transfer as
that is the main bottleneck in reference_data collection.


"""

import warnings
import logging
import time

from serial import Serial, PARITY_EVEN, STOPBITS_ONE
import numpy as np

import os

file_loc = os.path.join(os.path.dirname(__file__), 'data/')


class PhaseSensor:
    instances = []

    def __init__(self,
                 name: str = None,
                 port: str = "COM6",
                 number_sensors: int = 8,
                 gas: np.ndarray = None,
                 liq: np.ndarray = None):
        """
        :param name: something descriptive
        :param port: serial COM port
        :param number_sensors: number of ir sensors on a single setup
        :param gas: calibration values for gas
        :param liq: calibration values for liquid
        """
        self.serial_comm = Serial(port=port, baudrate=115200, parity=PARITY_EVEN, stopbits=STOPBITS_ONE,
                                      timeout=0.1)
        self.state = "standby"
        if name is None:
            self.name = "phase_sensor" 
        else:
            self.name = name

        # reference_data
        self.number_sensors = number_sensors
        self.buffer_level = 0
        self.buffer_max = 1_000
        self.data_buffer = np.empty([self.buffer_max, number_sensors + 1])  # "+1" is for time

        # reference_data to determine phase
        if gas is None:
            self.gas = None
        else:
            if gas.size == number_sensors:
                self.gas = gas
            else:
                raise ValueError(
                    f"Phase sensor || ({self.name}) {gas.size} values for gas calibration, but there are {number_sensors} "
                    f"number of sensors! (change PhaseSensor.number_sensors or PhaseSensor.gas)")
        if liq is None:
            self.liq = None
        else:
            if liq.size == number_sensors:
                self.liq = liq
            else:
                raise ValueError(
                    f"Phase sensor || ({self.name}) {liq.size} values for liquid calibration, but there are "
                    f"{number_sensors} number of sensors!"
                    f"(change PhaseSensor.number_sensors or PhaseSensor.liq)")

        self.mean = None
        self.pico_start_time = int(self.measure())
        self.cpu_start_time = time.time()

        # Extra stuff
        self.__class__.instances.append(self)
        logging.info(f'Phase sensor || ({self.name}) Initiated')

    def __repr__(self):
        return f"Phase Sensor\n\tclass_name: {self.name}\n\tstate: {self.state}"

    def measure_phase(self) -> np.ndarray:
        """
        This method will take one measurement from the phase sensor and return a True for liquid or False for gas.
        :return: np.array with time in column 0 and bools; True = Liquid, False = gas
        """
        raw_data = self.measure()
        if raw_data is None:
            return None
        if self.liq is None or self.gas is None:
            warnings.warn(f"Phase sensor || ({self.name}) has not yet been calibrated. (Run zero "
                          f"method.)")
            logging.warning(f"Phase sensor || ({self.name}) has not yet been calibrated. (Run "
                            f"zero method.)")
            return None

        raw_data[1:] = self.determine_phase(raw_data[1:], self.gas, self.liq)
        return raw_data

    def measure_mean(self, save: bool = True, smooth: bool = False) -> np.ndarray:
        """
        This method will take one measurement from the phase sensor and return the normalized to mean values.
        :param save: add date to buffer
        :param smooth: do exponential smoothing
        :return:
        """
        raw_data = self.measure()
        if raw_data is None:
            return None
        if self.mean is None:
            warnings.warn(f"Phase sensor || ({self.name}) has not yet had mean calculated yet."
                          "(Run get_mean method.)")
            logging.warning(f"Phase sensor || ({self.name}) has not yet had mean calculated yet."
                            "(Run get_mean method.)")
            return None
        raw_data[1:] = np.divide(np.multiply(raw_data[1:], 1000), self.mean)
        return raw_data

    def measure(self, save: bool = True, smooth: bool = False) -> np.array:
        """
        This method will take one measurement from the phase sensor.
        :param save: add date to buffer
        :param smooth: do exponential smoothing
        :return:
        """
        # repeatably send request for a "read"
        try:
            for _ in range(10):
                self.serial_comm.write("r".encode())
                message = self.serial_comm.read_until()
                message = message.decode()

                if message != "":  # Once get reply with reference_data, return
                    if message[0] == "d":  # confirm that the message is reference_data
                        data = self.data_decode(message)
                        try:
                            data[0] = data[0] - self.pico_start_time
                        except AttributeError:
                            return data[0]
                        if save:
                            if smooth:
                                a = 0.8
                                data = a * data + (1 - a) * self.data_buffer[self.buffer_level - 1, :]

                            self.add_data(data)
                        return data
        except UnicodeDecodeError:
            warnings.warn(f"Phase sensor || ({self.name}) not responding correctly; reset Pico.")
            logging.warning(f"Phase sensor || ({self.name}) not responding; reset Pico.")
            return None

        # if the sensor doesn't respond after 10 calls, stop and report warning
        warnings.warn(f"Phase sensor || ({self.name}) not responding.")
        logging.warning(f"Phase sensor || ({self.name}) not responding.")
        return None

    def add_data(self, data: np.array):
        """
        Adds reference_data to the buffer.
        :param data:
        :return:
        """
        self.data_buffer[self.buffer_level, :] = data
        self.buffer_level += 1
        # if buffer full, save it
        if self.buffer_level == self.buffer_max:
            self.save_buffer()

    def save_buffer(self):
        """
        Save reference_data in buffer to csv file.
        :return: None
        """
        logging.info(f"Phase sensor || ({self.name}) dataset saved.")
        np.savetxt(file_loc + str(self.name) + "_" + str(time.time()) + ".csv",
                   self.data_buffer[:self.buffer_level, :],
                   delimiter=",")
        self.buffer_level = 0

    def zero(self):
        pass

    def manual_zero(self, samples: int = 50):
        """
        Method used to get gas/liq parameters done by human step wise.
        Mainly useful for troubleshooting issues.
        :param samples: number of measurements
        :return: None, values are directly stored into self.gas ans self.liq
        """
        print("\n\nBeginning calibration:")
        print("Step 1 of 2) Fill sensor with air now. Press enter when read for measurement.")
        input()
        print("Collecting gas reference_data now. Do not tough anything. (may take a few seconds)")

        data = np.zeros((samples, self.number_sensors))
        for i in range(samples):
            data[i, :] = self.measure(save=False)[1:]

        self.gas = np.mean(data, axis=0)
        std = np.std(data, axis=0)
        print("Gas measurement done!")
        print(f"calibration values:")
        print(f"mean: \t{self.gas}")
        print(f"std:  \t{std}")

        print("\n\nBeginning calibration:")
        print("Step 2 of 2) Fill sensor with liquid now. Press enter when read for measurement.")
        input()
        print("Collecting liquid reference_data now. Do not tough anything. (may take a few seconds)")

        data = np.zeros((samples, self.number_sensors))
        for i in range(samples):
            data[i, :] = self.measure(save=False)[1:]

        self.liq = np.mean(data, axis=0)
        std = np.std(data, axis=0)
        print("Gas measurement done!")
        print(f"calibration values:")
        print(f"mean: \t{self.liq}")
        print(f"std:  \t{std}")
        logging.info(f"Phase sensor || ({self.name}) Manual calibration done." + "\n" +
                     f"Gas values: {self.gas}" + "\n"
                                                 f"Liquid values: {self.liq}"
                     )
        print("Press enter to continue.")
        input()

    def get_mean(self, num: int = 50):
        """
        This function can be called to get a mean of the current sensor state.
        :param num: number of measurements to get the mean
        :return:  None; sets the self.mean vaiable in the class
        """
        mean = np.empty((num, self.number_sensors))
        for i in range(num):
            mean[i, :] = self.measure()[1:]

        self.mean = np.sum(mean, axis=0) / num

    @staticmethod
    def data_decode(message: str) -> np.array:
        """
        This parses the message from the PICO into an numpy array.
        :param message: raw message from PICO.
        :return: reference_data in numpy array.
        """
        message = message.replace("d", "").replace("\n", "")
        _time, values = message.split("+")
        values = values.replace("[", "").replace("]", "")
        values = values.split(", ")
        return np.array([int(_time)] + [int(value) for value in values], dtype="uint64")

    @staticmethod
    def determine_phase(value: np.ndarray, gas: np.ndarray, liq: np.ndarray):
        """
        Determine phase from raw reference_data and zero reference_data.
        :param value: np.array of phase sensor reference_data
        :param gas: value of phase sensor when gas is flowing through it.
        :param liq: value of phase sensor when liquid is flowing through it.
        :return: np.array of bool; True = Liquid, False = gas
        """
        gas_diff = np.abs(np.subtract(value, gas))
        liq_diff = np.abs(np.subtract(value, liq))
        return liq_diff > gas_diff


def main():
    """
        Example code for a single phase sensor.
        You will likely need to change the COM port to match your devices.

        Output: Prints to screen reference_data and every 50 datapoint, the reference_data rate in Hz.
        """
    PS1 = PhaseSensor(name="in_phase_sensor", port="COM7")
    n = 100
    start = time.time()
    data_save = np.zeros((n, 9))
    np.set_printoptions(precision=3)
    try:
        for i in range(n):
            data = PS1.measure()
            time.sleep(.1)

            data_save[i, :] = data
            print(data)

    finally:
        np.savetxt("data3.csv", data_save, delimiter=",")

    print("Done")


if __name__ == '__main__':
    main()
