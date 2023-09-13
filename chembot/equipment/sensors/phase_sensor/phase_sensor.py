import functools
import pathlib
import logging
import time

from serial import Serial
import numpy as np
from unitpy import Unit, Quantity

from chembot.configuration import config, create_folder
from chembot.equipment.sensors.sensor import Sensor
from chembot.equipment.sensors.controllers.controller import Controller
from chembot.utils.buffers.buffers import Buffer
from chembot.utils.buffers.buffer_ring import BufferRingTime
from chembot.utils.algorithms.change_detection import CUSUM

logger = logging.getLogger(config.root_logger_name + ".phase_sensor")


def format_pin(pin: int, mode: int) -> str:
    return f"{pin:02}{mode}"


def parse_measurement(message: str, dtype=np.int64) -> np.ndarray:
    return np.array(message.split(","), dtype=dtype)


class Slug:
    sensor_spacer = 0.95 * Unit.cm
    tube_diameter = 0.0762 * Unit.cm
    __slots__ = ("time_start_1", "time_end_1", "time_start_2", "time_end_2", "_length", "_velocity")

    def __init__(self,
                 time_start_1: float | int,
                 time_end_1: float | int = None,
                 time_start_2: float | int = None,
                 time_end_2: float | int = None,
                 velocity: Quantity | None = None
                 ):
        self.time_start_1 = time_start_1
        self.time_end_1 = time_end_1
        self.time_start_2 = time_start_2
        self.time_end_2 = time_end_2
        self._length = None
        self._velocity = velocity

    def __str__(self):
        if self.volume is not None:
            text = f"vel:{self.velocity:3.2f}, len: {self.length:3.2f}, vol:{self.volume:3.2f}"
        elif self.time_span:
            text = f"start: {self.time_start_1:3.2f}"
            if self.velocity is not None:
                text += f", velocity: {self.velocity:3.2f})"
        else:
            text = f"start: {self.time_start_1:3.2f}, No end detected"

        return text

    @property
    def time_span(self) -> Quantity | None:
        if self.time_end_1 is None:
            return None
        t = self.time_end_1 - self.time_start_1
        if isinstance(t, Quantity):
            return t
        return t * Unit.s

    @property
    def time_offset(self):
        if self.is_complete:
            t = (self.time_start_2 - self.time_start_1 + self.time_end_2 - self.time_end_1) / 2
            if isinstance(t, Quantity):
                return t
            return t * Unit.s
        return None

    @property
    def is_complete(self) -> bool:
        return not (self.time_end_1 is None or self.time_end_2 is None or self.time_start_2 is None)

    @property
    def velocity(self) -> Quantity | None:
        if self._velocity is None:
            if not self.is_complete:
                return None
            self._velocity = self.sensor_spacer / self.time_span

        return self._velocity.to("mm/s")

    @property
    def length(self) -> Quantity | None:
        if self._length is None:
            if self.velocity is None or self.time_span is None:
                return None
            self._length = self.velocity * self.time_span

        return self._length.to('mm')

    @property
    def volume(self) -> Quantity | None:
        if self.length is None:
            return None
        return (self.length * np.pi * (self.tube_diameter / 2) ** 2).to("uL")


def main2(path):
    velocity = 0.3 * Unit("ml/min") / (np.pi * (Slug.tube_diameter / 2) ** 2)
    data = np.genfromtxt(path, delimiter=",")
    data[:, 0] = data[:, 0] - data[0, 0]

    algorithm = CUSUM()
    slugs = []
    up = np.zeros(data.shape[0])
    down = np.zeros(data.shape[0])
    for i in range(data.shape[0]):
        new_data_point = data[i, 1]
        event = algorithm.add_data(new_data_point)
        if event is CUSUM.States.up:
            slugs.append(Slug(time_start_1=data[i, 0], velocity=velocity))
        if event is CUSUM.States.down and slugs:
            slugs[-1].time_end_1 = data[i, 0]


class PhaseSensor(Sensor):
    """
    signal increase when gas -> liquid
    """
    dtype = np.int16
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
                 name: str,
                 port: str = "COM6",
                 # number_sensors: int = 2,
                 controllers: list[Controller] | Controller = None,
                 buffer: Buffer = None
                 ):
        number_sensors = 2
        if buffer is None:
            buffer = BufferRingTime(self._data_path / name, np.zeros((10_000, number_sensors), dtype=self.dtype))

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
        # logger.debug(f"send: {message}")
        self.serial.write(message.encode(config.encoding))

    def _read(self, read_bytes: int) -> str:
        message = self.serial.read(read_bytes).decode(config.encoding)
        # logger.debug(f"receive: {message}")
        return message.strip("\n")

    def _read_until(self, symbol: str = "\n") -> str:
        message = self.serial.readline().decode(config.encoding)
        return message.strip(symbol)

    def _write_and_read(self, message: str, expected_reply: str = None, reply_processing: callable = None):
        n = 3  # give it 3 tries to work
        for i in range(n):
            self._write(message)
            try:
                reply = self._read_until()
                if expected_reply is not None and reply[0] != expected_reply:
                    raise ValueError(f"Unexpected reply from pico when sending message: {message}.\nReceived: {reply}")
                if reply_processing is not None:
                    try:
                        return reply_processing(reply)
                    except Exception as ee:
                        raise ValueError(f"Error parsing a pico reply when sending message: {message}.\nReceived: "
                                         f"{reply}")
                return reply

            except ValueError as e:
                if i > n-1:
                    self.serial.flushInput()
                    continue
                if "reply" in locals():
                    print("reply:", reply)  # noqa
                if self.serial.in_waiting > 0:
                    print("in buffer:", self.serial.read_all())
                raise e

    def _activate(self):
        self.serial.flushInput()
        self.serial.flushOutput()
        reply = self._write_and_read("v", "v")
        self.pico_version = reply[1:]

    def _deactivate(self):
        self._write_and_read("r", "r")

    def _stop(self):
        super()._stop()
        time.sleep(2)  # allow for last reads to finish before writing to leds
        self.write_leds_power(False)
        self.serial.flushOutput()
        self.serial.flushInput()

    def write_measure(self, pins: tuple[int, int] = (0, 1), modes: tuple[int, int] = (1, 1)) -> np.ndarray:
        if self.serial.in_waiting != 0:
            self.serial.flushInput()
        if not self.led_on:
            self.write_leds_power(on=True)

        return self._write_and_read(  # noqa
            message="s" + "".join(format_pin(pin, mode) for pin, mode in zip(pins, modes)),
            reply_processing=functools.partial(parse_measurement, {"dtype": self.dtype})
        )

    def write_gain(self, gain: int = 1):
        """

        Parameters
        ----------
        gain:
            range: [1, 2, 4, 8, 16]
        """
        self._write_and_read(f"g{gain:02}", "g")

    def write_leds_power(self, on: bool = False):
        """
        (flipped from normal due to transistors, pull down voltage to turn on)

        Parameters
        ----------
        on:
            True = led on = value sent: 0
            False = led off = value sent: 1

        """
        self._write_and_read(f"d{int(not on)}", "d")
        time.sleep(0.1)  # to give time for power up
        self._led_on = on

    def write_offset_voltage(self, offset_voltage: int | float = 0):
        """

        Parameters
        ----------
        offset_voltage:
            range: [0:5]
        """
        self._write_and_read(f"o{offset_voltage:.06}", "o")

    def write_auto_offset_gain(self, gain: int = 16):
        """

        Parameters
        ----------
        gain:
            set final desired gain

        """
        self.write_gain(1)

        n = 10
        self.write_leds_power(on=True)
        data = np.zeros((n, 2), dtype=np.int16)
        for i in range(n):
            data[i, :] = self.write_measure((0, 1), (0, 0))

        # 16 bit resolution adc = 2**16 -1   (minus 1 is it starts at zero)
        # divide by 2 as the 16 bit is center at zero with both positive and negative
        # 5 volts is used
        voltage = np.mean(np.mean(data, axis=0)) / ((2 ** 16 - 1) / 2) * 4.096
        print(voltage)
        voltage += self.gains[gain] / 2

        self.write_offset_voltage(voltage)
        self.write_gain(gain)
        self.write_leds_power(on=False)

    def write_next_slug(self, slug_volume: Quantity = None, slug_length: Quantity = None):


        flow_rate = self.rabbit.send(read_pump_state)
