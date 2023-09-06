import pathlib
import logging
import time

from serial import Serial
import numpy as np

from chembot.configuration import config, create_folder
from chembot.equipment.sensors.sensor import Sensor
from chembot.equipment.sensors.controllers.controller import Controller
from chembot.utils.buffers.buffers import Buffer
from chembot.utils.buffers.buffer_ring import BufferRingTime

logger = logging.getLogger(config.root_logger_name + ".phase_sensor")


def format_pin(pin: int, mode: int) -> str:
    return f"{pin:02}{mode}"


class PhaseSensor(Sensor):
    """
    signal increase when gas -> liquid
    """
    gains = {
        1: 4.096,
        2: 2.048,
        4: 1.024,
        8: 0.512,
        16: 0.256
    }
    pins = (0, 1)
    modes = (0, 1)

    @property
    def _data_path(self):
        path = config.data_directory / pathlib.Path("phase_sensor")
        create_folder(path)
        return path

    def __init__(self,
                 name: str = None,
                 port: str = "COM6",
                 number_sensors: int = 2,
                 controllers: list[Controller] | Controller = None,
                 buffer: Buffer = None
                 ):
        dtype = "uint64"
        if buffer is None:
            buffer = BufferRingTime(self._data_path / (name + ".csv"), dtype, (10_000, number_sensors), 500)

        super().__init__(name, buffer, controllers)
        self.serial = Serial(port=port)

        self.number_sensors = number_sensors
        self.gain = 1
        self.offset_voltage = 0
        self._led_on = False

    def __repr__(self):
        return f"Phase Sensor\n\tclass_name: {self.name}\n\tstate: {self.state}"

    @property
    def led_on(self) -> bool:
        return self._led_on

    def _write(self, message: str):
        message = message + "\n"
        # logger.info(f"send: {message}")
        self.serial.write(message.encode(config.encoding))

    def _read(self, read_bytes: int) -> str:
        message = self.serial.read(read_bytes).decode(config.encoding)
        # logger.info(f"receive: {message}")
        return message.strip("\n")

    def _read_until(self, symbol: str = "\n") -> str:
        message = self.serial.readline().decode(config.encoding)
        return message.strip(symbol)

    def _activate(self):
        self.serial.flushInput()
        self.serial.flushOutput()
        self._write("v")
        reply = self._read_until()
        if reply[0] != "v":
            raise ValueError(f"Unexpected reply from Pico during activation.\n reply:{reply}")
        self.pico_version = reply[1:]

    def _deactivate(self):
        self._write("r")
        reply = self._read_until()
        if reply[0] != "r":
            raise ValueError(f"Unexpected reply from Pico when deactivating.\n reply:{reply}")

    def _stop(self):
        super()._stop()
        self.write_leds_power(False)
        self.serial.flushOutput()
        self.serial.flushInput()

    def write_measure(self, pins: tuple[int] = (0, 1), modes: tuple[int] = (1, 1)) -> np.ndarray:
        if self.serial.in_waiting != 0:
            self.serial.flushInput()
        if not self.led_on:
            self.write_leds_power(on=True)

        self._write("s" + "".join(format_pin(pin, mode) for pin, mode in zip(pins, modes)))
        try:
            reply = self._read_until()
            return np.array(reply.split(","), dtype=np.int16)
        except ValueError as e:
            if "reply" in locals():
                print(reply)
            if self.serial.in_waiting > 0:
                print(self.serial.read_all())
            raise e

    def write_gain(self, value: int = 1):
        """ 1,2,4,8,16"""
        self._write(f"g{value:02}")
        reply = self._read_until()
        if reply[0] != "g":
            raise ValueError(f"unexpected reply from pico. received: {reply}")

    def write_leds_power(self, on: bool = False):
        """
        (flipped from normal due to transistors, pull down voltage to turn on)

        Parameters
        ----------
        on:
            True = led on = value sent: 0
            False = led off = value sent: 1

        """
        self._write(f"d{int(not on)}")
        reply = self._read_until()
        if reply[0] != "d":
            raise ValueError(f"unexpected reply from pico. received: {reply}")
        time.sleep(0.1)  # to give time for power up
        self._led_on = on

    def write_auto_offset_gain(self, gain: int = 16):
        self.write_gain(1)

        n = 10
        self.write_leds_power(on=True)
        data = np.zeros((n, 2), dtype=np.int16)
        for i in range(n):
            data[i, :] = self.write_measure([0, 1], [0, 0])

        # 16 bit resolution adc = 2**16 -1   (minus 1 is it starts at zero)
        # divide by 2 as the 16 bit is center at zero with both positive and negative
        # 5 volts is used
        voltage = np.mean(np.mean(data, axis=0)) / ((2 ** 16 - 1) / 2) * 4.096
        print(voltage)
        voltage += self.gains[gain] / 2

        # write DAC voltage
        self._write(f"o{voltage:.06}")
        reply = self._read_until()
        if reply[0] != "o":
            raise ValueError(f"unexpected reply from pico: {reply}")

        self.write_gain(gain)
        self.write_leds_power(on=False)

    # def write_measure_phase(self, number_of_measurements: int = 1) -> np.ndarray:
    #     data = self._measure(number_of_measurements)
    #     data = (data-self.gas_background) / (self.liquid_background - self.gas_background)
    #     return np.round(data).astype(bool)
