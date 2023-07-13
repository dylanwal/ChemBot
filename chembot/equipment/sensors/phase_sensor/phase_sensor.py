
import pathlib
import logging

from serial import Serial, PARITY_EVEN, STOPBITS_ONE
import numpy as np

from chembot.configuration import config, create_folder
from chembot.equipment.sensors.sensor import Sensor
from chembot.equipment.sensors.buffer_ring import BufferRing

logger = logging.getLogger(config.root_logger_name + ".phase_sensor")


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


class PhaseSensor(Sensor):
    _data_path = config.data_directory / pathlib.Path("phase_sensor")
    create_folder(_data_path)

    def __init__(self,
                 name: str = None,
                 port: str = "COM6",
                 number_sensors: int = 8
                 ):
        super().__init__(name)
        self.serial = Serial(port=port, baudrate=115200, parity=PARITY_EVEN, stopbits=STOPBITS_ONE,
                             timeout=0.1)

        self.number_sensors = number_sensors
        self._background = np.zeros(self.number_sensors, dtype="uint16")

        self.buffer = BufferRing(self._data_path / self.name, "uint16", (10_000, 8), 500)

    def __repr__(self):
        return f"Phase Sensor\n\tclass_name: {self.name}\n\tstate: {self.state}"

    def _write(self, message: str):
        message = message + "\n"
        self.serial.write(message.encode(config.encoding))

    def _read(self, read_bytes: int) -> str:
        message = self.serial.read(read_bytes).decode(config.encoding)
        return message.strip("\n")

    def _read_until(self, symbol: str = "\n"):
        reply = self.serial.read_until(symbol)
        return reply.strip(symbol)

    def _activate(self):
        self.serial.flushInput()
        self.serial.flushOutput()
        self.serial.write("v")
        reply = self._read_until()
        if reply[0] != "v":
            raise ValueError(f"Unexpected reply from Pico during activation.\n reply:{reply}")
        self.pico_version = reply[1:]

    def _deactivate(self):
        self.serial.write("r")
        reply = self._read_until()
        if reply != "r":
            raise ValueError(f"Unexpected reply from Pico when deactivating.\n reply:{reply}")

    def _stop(self):
        self.serial.write("r")
        reply = self._read_until()
        if reply != "r":
            raise ValueError(f"Unexpected reply from Pico when deactivating.\n reply:{reply}")

    def _measure(self, number_of_measurements: int = 1) -> np.ndarray:
        if self.serial.in_waiting != 0:
            self.serial.flushInput()

        self._write(f"w{number_of_measurements:02}")
        data = np.zeros((number_of_measurements, self.number_sensors), dtype="uint32")
        for i in range(number_of_measurements):
            reply = self._read_until()
            if reply[0] != "w":
                raise ValueError(f"Unexpected reply from Pico when measuring from phase sensor.\n reply:{reply}")
            data[i] = np.array(np.array(reply[1:].split(',')), dtype="uint32")

        return data

    def write_measure(self, number_of_measurements: int = 1) -> np.ndarray:
        data = self._measure(number_of_measurements)
        data -= self._background
        return data

    def read_background(self) -> np.ndarray:
        return self._background

    def write_background(self, number_of_measurements: int = 25):
        data = self._measure(number_of_measurements)
        self._background = np.mean(data, axis=0)

    def write_continuously_measure(self):
        theading
        for i in range(100):
            self.buffer.add_data(self.write_measure())
