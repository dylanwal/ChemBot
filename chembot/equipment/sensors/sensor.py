import time
import abc
import threading

from chembot.equipment.equipment import Equipment
from chembot.equipment.sensors.controllers.controller import Controller
from chembot.equipment.sensors.buffers.buffers import Buffer
from chembot.utils.algorithms.data_filtering import Filter


class Sensor(Equipment, abc.ABC):

    def __init__(self, name: str, buffer: Buffer, controllers: list[Controller] | Controller = None):
        super().__init__(name)

        if not isinstance(controllers, list):
            controllers = [controllers]
        self.controllers = controllers
        self.buffer = buffer

        self.time_between_measurements = 0
        self.filter_ = None
        self._thread = threading.Thread(target=self._thread_measure)
        self._stop_thread = False

    @abc.abstractmethod
    def write_measure(self):
        pass

    def write_measure_continuously(self, time_between_measurements: float = 1, filter_: Filter = None):
        """
        take measurements continuously

        Parameters
        ----------
        time_between_measurements:
            in seconds
            this is the fastest it will measure at; but it could be slower depending on the time it takes to take the
            measurement
            range: [0:10000]
        filter_:
            algorithm to filter data
        """
        if self._thread.is_alive():
            raise ValueError("{self.name} measurement thread is already and can't be restarted.")

        self.time_between_measurements = time_between_measurements
        self.filter_ = filter_
        self._thread.start()

    def _thread_measure(self):
        next_measurement_time = time.time()
        while True:

            # measurement timing
            if time.time() < next_measurement_time:
                continue
            next_measurement_time += self.time_between_measurements

            # take measurement
            self.buffer.add_data(self.write_measure())

            if self.filter_ is not None:
                self.filter_.process_data(self.buffer)

            # check controller
            if self.controllers:
                for controller in self.controllers:
                    controller.trigger(self.buffer)

            # stop
            if self._stop_thread:
                self._stop_thread = False
                self.buffer.reset()
                break
