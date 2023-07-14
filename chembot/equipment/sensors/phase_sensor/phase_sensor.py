import pathlib
import logging

from serial import Serial, PARITY_EVEN, STOPBITS_ONE
import numpy as np

from chembot.configuration import config, create_folder
from chembot.equipment.sensors.sensor import Sensor
from chembot.equipment.sensors.controllers.controller import Controller
from chembot.equipment.sensors.buffers.buffers import Buffer
from equipment.sensors.buffers.buffer_ring import BufferRingTime

logger = logging.getLogger(config.root_logger_name + ".phase_sensor")


class PhaseSensor(Sensor):
    @property
    def _data_path(self):
        path = config.data_directory / pathlib.Path("phase_sensor")
        create_folder(path)
        return path

    def __init__(self,
                 name: str = None,
                 port: str = "COM6",
                 number_sensors: int = 8,
                 controllers: list[Controller] | Controller = None,
                 buffer: Buffer = None
                 ):
        dtype = "uint16"
        if buffer is None:
            buffer = BufferRingTime(self._data_path / self.name, dtype, (10_000, number_sensors), 500)

        super().__init__(name, buffer, controllers)
        self.serial = Serial(port=port, baudrate=115200, parity=PARITY_EVEN, stopbits=STOPBITS_ONE, timeout=0.1)
        self.number_sensors = number_sensors
        self.gas_background = np.zeros(self.number_sensors, dtype=dtype)
        self.liquid_background = np.zeros(self.number_sensors, dtype=dtype)

    def __repr__(self):
        return f"Phase Sensor\n\tclass_name: {self.name}\n\tstate: {self.state}"

    @property
    def measurement_frequency(self) -> float:
        return 1/self.time_between_measurements

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
        self._stop_thread = True
        self.serial.flushOutput()
        self.serial.flushInput()

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
        return data

    def write_measure_phase(self, number_of_measurements: int = 1) -> np.ndarray:
        data = self._measure(number_of_measurements)
        data = (data-self.gas_background) / (self.liquid_background - self.gas_background)
        return np.round(data).astype(bool)

    def read_gas_background(self) -> np.ndarray:
        return self.gas_background

    def write_measure_gas(self, number_of_measurements: int = 25):
        data = self._measure(number_of_measurements)
        self.gas_background = np.mean(data, axis=0)

    def read_liquid_background(self) -> np.ndarray:
        return self.liquid_background

    def write_measure_liquid(self, number_of_measurements: int = 25):
        data = self._measure(number_of_measurements)
        self.liquid_background = np.mean(data, axis=0)
