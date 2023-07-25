import time
import abc
import threading
import logging

from chembot.configuration import config
from chembot.equipment.equipment import Equipment
from chembot.equipment.sensors.controllers.controller import Controller
from chembot.equipment.sensors.buffers.buffers import Buffer
from chembot.utils.algorithms.data_filtering import Filter

logger = logging.getLogger(config.root_logger_name + ".sensor")


class Sensor(Equipment, abc.ABC):

    def __init__(self, name: str, buffer: Buffer, controllers: list[Controller] | Controller = None):
        super().__init__(name)

        if controllers is None:
            controllers = []
        elif not isinstance(controllers, list):
            controllers = [controllers]
        self.controllers = controllers
        self.buffer = buffer

        self.time_between_measurements = 0
        self.filter_ = None
        self._stop_thread = True
        self._thread_func = self.write_measure
        self._thread = threading.Thread(target=self._thread_measure)
        self._thread.start()

    def _stop(self):
        self._stop_thread = True

    @abc.abstractmethod
    def write_measure(self):
        pass

    def write_measure_continuously(self,
                                   func: str = "write_measure",
                                   time_between_measurements: float = 1,
                                   filter_: Filter = None
                                   ):
        """
        take measurements continuously

        Parameters
        ----------
        func:
            function to be called
        time_between_measurements:
            in seconds
            this is the fastest it will measure at; but it could be slower depending on the time it takes to take the
            measurement
            range: [0:10000]
        filter_:
            algorithm to filter data
        """
        self._thread_func = getattr(self, func)
        self.time_between_measurements = time_between_measurements
        self.filter_ = filter_
        self._stop_thread = False

    def _thread_measure(self):
        main_thread = threading.main_thread()
        next_measurement_time = time.time()
        while True:
            if not main_thread.is_alive():
                break
            if self._stop_thread:
                time.sleep(0.1)
                continue

            logger.warning("thread active")
            while True:
                # measurement timing
                if time.time() < next_measurement_time:
                    time.sleep(0.0003)
                    continue
                next_measurement_time = time.time() + self.time_between_measurements

                # take measurement
                self.buffer.add_data(self._thread_func())

                if self.filter_ is not None:
                    self.filter_.process_data(self.buffer)

                # check controller
                if self.controllers:
                    for controller in self.controllers:
                        controller.trigger(self.buffer)

                # stop
                if self._stop_thread:
                    if self.buffer.save_data:
                        self.buffer.save_and_reset()
                    else:
                        self.buffer.reset()
                    break
