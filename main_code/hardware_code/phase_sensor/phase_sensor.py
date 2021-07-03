"""
Phase Sensor Class

"""

import warnings
import logging
from time import time

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

        :param name:
        :param port:
        """

        # Check to see if serial port taken
        for sensor in self.instances:
            if sensor.port == port:
                raise ValueError("Serial port already taken.")
        self.port = port

        # Setup communication
        self.serial_comm = Serial(port=port, baudrate=57600, parity=PARITY_EVEN, stopbits=STOPBITS_ONE, timeout=0.1)

        self.state = "standby"
        if name is None:
            self.name = "phase_sensor" + str(len(self.instance))
        else:
            self.name = name

        # data
        self.number_sensors = number_sensors
        self.buffer_level = 0
        self.buffer_max = 10_000
        self.data_buffer = np.empty([self.buffer_max, number_sensors+1])  # "+1" is for time

        # data to determine phase
        if gas is None:
            self.gas = None
        else:
            if gas.size == number_sensors:
                self.gas = gas
            else:
                raise ValueError(f"Phase Sensor: {gas.size} values for gas calibration, but there are {number_sensors} "
                                 f"number of sensors! (change PhaseSensor.number_sensors or PhaseSensor.gas)")
        if liq is None:
            self.liq = None
        else:
            if liq.size == number_sensors:
                self.liq = liq
            else:
                raise ValueError(f"Phase Sensor: {liq.size} values for liquid calibration, but there are "
                                 f"{number_sensors} number of sensors!"
                                 f"(change PhaseSensor.number_sensors or PhaseSensor.liq)")

        self.mean = None
        self.pico_start_time = int(self.measure())
        self.cpu_start_time = time()

        # Extra stuff
        self.__class__.instances.append(self)
        logging.info(f'Phase Sensor Initiated:\n\t port: {self.port}')

    def __repr__(self):
        return f"Phase Sensor\n\tport: {self.port}\n\tstate: {self.state}"

    def measure_phase(self):
        """

        :return: np.array with time in column 0 and bools; True = Liquid, False = gas
        """
        raw_data = self.measure()
        if raw_data is None:
            return None
        if self.liq is None or self.gas is None:
            warnings.warn(f"Phase sensor(name: {self.name}; port:{self.port}) has not yet been calibrated. (Run zero "
                          f"method.)")
            logging.warning(f"Phase sensor(name: {self.name}; port:{self.port}) has not yet been calibrated. (Run "
                            f"zero method.)")
            return None

        raw_data[1:] = self.determine_phase(raw_data[1:], self.gas, self.liq)
        return raw_data

    def measure_mean(self, save: bool = True, smooth: bool = False)-> np.array:
        """

        :param save: add date to buffer
        :param smooth: do exponential smoothing
        :return:
        """
        raw_data = self.measure()
        if raw_data is None:
            return None
        if self.mean is None:
            warnings.warn(f"Phase sensor(name: {self.name}; port:{self.port}) has not yet had mean calculated yet."
                          "(Run get_mean method.)")
            logging.warning(f"Phase sensor(name: {self.name}; port:{self.port}) has not yet had mean calculated yet."
                            "(Run get_mean method.)")
            return None
        raw_data[1:] = np.divide(np.multiply(raw_data[1:], 1000), self.mean)
        return raw_data

    def measure(self, save: bool = True, smooth: bool = False) -> np.array:
        """
        This method will take only one single measurement from the phase sensor.
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

                if message != "":  # Once get reply with data, return
                    if message[0] == "d":  # confirm that the message is data
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
            warnings.warn(f"Phase sensor(name: {self.name}; port:{self.port}) not responding correctly; reset Pico.")
            logging.warning(f"Phase sensor(name: {self.name}; port:{self.port}) not responding; reset Pico.")
            return None

        # if the sensor doesn't respond after 20 calls, stop and report warning
        warnings.warn(f"Phase sensor(name: {self.name}; port:{self.port}) not responding.")
        logging.warning(f"Phase sensor(name: {self.name}; port:{self.port}) not responding.")
        return None

    def add_data(self, data: np.array):
        """
        Adds data to the buffer.
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
        Save data in buffer to csv file.
        :return: None
        """
        logging.info(f"{self.name}: dataset saved.")
        np.savetxt(file_loc + str(self.name) + "_" + str(time()) + ".csv",
                   self.data_buffer[:self.buffer_level, :],
                   delimiter=",")
        self.buffer_level = 0

    def zero(self, manual: bool = False, samples: int = 50):
        """
        Method used to get gas/liq parameters
        :param manual: done by human if True
        :param samples: number of measurements
        :return: None, values are directly stored into self.gas ans self.liq
        """
        if manual is True:
            print("\n\nBeginning calibration:")
            print("Step 1 of 2) Fill sensor with air now. Press enter when read for measurement.")
            input()
            print("Collecting gas data now. Do not tough anything. (may take a few seconds)")

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
            print("Collecting liquid data now. Do not tough anything. (may take a few seconds)")

            data = np.zeros((samples, self.number_sensors))
            for i in range(samples):
                data[i, :] = self.measure(save=False)[1:]

            self.liq = np.mean(data, axis=0)
            std = np.std(data, axis=0)
            print("Gas measurement done!")
            print(f"calibration values:")
            print(f"mean: \t{self.liq}")
            print(f"std:  \t{std}")
            logging.info(f"PhaseSensor: Manual calibration done on {self.name}." + "\n" +
                         f"Gas values: {self.gas}" + "\n"
                         f"Liquid values: {self.liq}"
                         )
            print("Press enter to continue.")
            input()
        else:
            pass

    def get_mean(self, num: int = 50):
        mean = np.empty((num, self.number_sensors))
        for i in range(num):
            mean[i, :] = self.measure()[1:]

        self.mean = np.sum(mean, axis=0)/num

    @staticmethod
    def data_decode(message: str) -> np.array:
        message = message.replace("d", "").replace("\n", "")
        _time, values = message.split("+")
        values = values.replace("[", "").replace("]", "")
        values = values.split(", ")
        return np.array([int(_time)]+[int(value) for value in values], dtype="uint64")

    @staticmethod
    def determine_phase(value: np.ndarray, gas: np.ndarray, liq: np.ndarray):
        """
        Determine phase from raw data and zero data.
        :param value: np.array of phase sensor data
        :param gas: value of phase sensor when gas is flowing through it.
        :param liq: value of phase sensor when liquid is flowing through it.
        :return: np.array of bool; True = Liquid, False = gas
        """
        gas_diff = np.abs(np.subtract(value, gas))
        liq_diff = np.abs(np.subtract(value, liq))
        return liq_diff > gas_diff


if __name__ == '__main__':

    # import sys
    # import logging
    #
    # logger = logging.getLogger(__name__)
    # handler = logging.StreamHandler(stream=sys.stdout)
    # logger.addHandler(handler)
    #
    #
    # def handle_exception(exc_type, exc_value, exc_traceback):
    #     if issubclass(exc_type, KeyboardInterrupt):
    #         sys.__excepthook__(exc_type, exc_value, exc_traceback)
    #         return
    #
    #     logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    #
    #
    # sys.excepthook = handle_exception
    #

    #
    logging.basicConfig(filename=r'.\testing.log',
                        level=logging.DEBUG,
                        format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')
    logging.info("\n\n")
    logging.info("---------------------------------------------------")
    logging.info("---------------------------------------------------")




    # # Testing decode function
    # test_message = "428475330+[80903, 82807, 96221, 79117, 546457, 45645]\n"
    # print(PhaseSensor.data_decode(test_message))

    # testing
    from time import time
    from main_code.utils import sig_figs
    gas = np.array([75204.32, 69611.18, 85343.46, 73813.6])
    liq = np.array([80279.38, 75647.18, 89400.96, 78617.64])
    in_phase_sensor = PhaseSensor(name="in_phase_sensor", number_sensors=4)
    # in_phase_sensor.zero(manual=True)
    # in_phase_sensor.get_mean()
    start = time()
    k = 0
    np.set_printoptions(precision=3)
    for _ in range(100):
        k += 1
        data = in_phase_sensor.measure()
        print(data[1:])
        if k == 20:
            k = 0
            end = time()
            print(f"data rate: {20/(end-start)}")
            start = end
