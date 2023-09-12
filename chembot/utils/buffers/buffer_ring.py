import abc
import os
import pathlib
import queue
import threading
import time
import logging

import numpy as np

logger = logging.getLogger("buffer")


class BufferRing:
    """
    The buffer ring is an efficient way to reuse the same memory over and over  again for data streaming in.
    """
    DEFAULT_LENGTH = 1000

    def __init__(self, buffer: np.ndarray = None, length: int = None):
        self.buffer = buffer
        self.position = -1
        self.length = length

    def __str__(self):
        return f"buffer: {self.shape}, position: {self.position}"

    def __repr__(self):
        return self.__str__()

    @property
    def shape(self) -> tuple[int, int]:
        return self.buffer.shape

    @property
    def dtype(self):
        return self.buffer.dtype

    @property
    def last_measurement(self) -> np.ndarray:
        return self.buffer[self.position, :]

    def add_data(self, data: int | float | np.ndarray):
        try:
            # try-except is used for improved performance
            self._update_position()  # will raise an Attribute error if no buffer created yet
            self.buffer[self.position, :] = data
        except AttributeError as e:
            if self.buffer is None:
                # create buffer if they didn't exist
                self._create_buffer(data)
                self.buffer[self.position, :] = data
            else:
                raise e

    def _update_position(self):
        if self.position == self.buffer.shape[0] - 1:
            self.position = 0
        else:
            self.position += 1

    def _create_buffer(self, data: int | float | np.ndarray):
        if self.length is not None:
            length = self.length
        else:
            length = self.DEFAULT_LENGTH
        if isinstance(data, int):
            self.buffer = np.zeros((length, 1), dtype=np.int64)
        elif isinstance(data, float):
            self.buffer = np.zeros((length, 1), dtype=np.float64)
        elif isinstance(data, np.ndarray):
            self.buffer = np.zeros((length, data.shape[0]), dtype=data.dtype)
        else:
            raise TypeError("Invalid type")

    def get_data(self, start: int, end: int) -> np.ndarray:
        if start > end:
            return np.concatenate((self.buffer[start:, :], self.buffer[0:end, :]))
        return self.buffer[start:end, :]


class BufferRingTime(BufferRing):
    """
    The buffer ring is an efficient way to reuse the same memory over and over  again for data streaming in.
    """

    def __init__(self, buffer: np.ndarray = None, buffer_time: np.ndarray = None, length: int = None):
        super().__init__(buffer, length)
        if buffer is not None:
            self.buffer_time = np.zeros(self.buffer.shape[0], dtype=np.f64)
        self.buffer_time = buffer_time

    @property
    def last_time(self) -> float:
        return self.buffer_time[self.position]

    def add_data(self, data: int | float | np.ndarray):
        super(BufferRingTime, self).add_data(data)
        self.buffer_time[self.position] = time.time()

    def _create_buffer(self, data: int | float | np.ndarray):
        super(BufferRingTime, self).add_data(data)
        self.buffer_time = np.zeros(self.buffer.shape[0], dtype=np.f64)

    def get_data(self, start: int, end: int, merge: bool = True) -> tuple[np.ndarray, np.ndarray] | np.ndarray:
        if start > end:
            data = (
                np.concatenate((self.buffer_time[start:], self.buffer_time[:end])),
                np.concatenate((self.buffer[start:, :], self.buffer[0:end, :]))
                    )
        else:
            data = (
                self.buffer_time[start:end],
                self.buffer[start:end, :]
            )
        if merge:
            data = np.concatenate(data, axis=1)

        return data


class SavingMixin(abc.ABC):
    file_size_limit = 30_000

    def __init__(self, path: str | pathlib.Path, queue_size: int, saving: bool = True):
        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path)
        self.path = path

        # stuff for saving via thread
        self.saving = saving
        self.data_queue = queue.Queue(maxsize=queue_size)

        self._thread = threading.Thread(target=self._thread_save)
        self._file_counter = 0
        self._resets = 0
        self._pause_saving = False

        if self.saving:
            self._thread.start()

    def get_file_path(self, index: int) -> pathlib.Path:
        path = self.path
        if self._resets > 0:
            path = path.with_stem(path.stem + "_reset" + str(self._resets))
        path = path.with_stem(path.stem + "_" + str(index))
        path = path.with_suffix(".csv")

        # check for existing path and add
        return path

    def _thread_save(self):
        """
        this function periodically saves data from the buffer to csv.
        this function is called by the thread.
        """
        main_thread = threading.main_thread()
        index = -1
        close_thread = False
        while not close_thread:
            index += 1  # counter for index path name for each new file
            counter = 0  # counter when to start a new file
            with open(self.get_file_path(index), mode="w", encoding="utf-8") as f:
                while True:
                    try:
                        data: np.ndarray = self.data_queue.get(timeout=0.2)  # blocking
                    except queue.Empty:
                        if self._pause_saving:
                            self._pause_saving = False
                            break
                        elif not main_thread.is_alive() and not close_thread:
                            self.save_all()
                            self.close_thread = True
                            continue

                        # exit once everything is saved close thread
                        break

                    # write row
                    logger.info("saving")
                    for row in data:
                        f.write(','.join(str(i) for i in row))
                        f.write('\n')

                    # check if we have hit row limit for current file
                    counter += data.shape[0]
                    if counter > self.file_size_limit:
                        break

            if counter == 0:
                os.remove(self.get_file_path(index))

    @abc.abstractmethod
    def save_all(self):
        ...


class BufferRingSavable(BufferRing, SavingMixin):
    """
    The buffer ring is an efficient way to reuse the same memory over and over  again for data streaming in.
    It will periodically save data to a csv for long term storage.

    threading is used to ensure data can still be added while the save is happening.
    Note that data is saved from the buffer at the same time data is being written to it 'creating a data race'.
    This is not a problem if the buffer is big enough to not be reading and writing to the same cell at the same
    time. A check is added to stop if buffer is overfilled.

    """

    def __init__(self,
                 path: pathlib.Path,
                 buffer: np.ndarray = None,
                 number_of_rows_per_save: int = 1000,
                 length: int = None
                 ):
        """

        Parameters
        ----------
        path:
            location where data will be saved.
        buffer:
            buffer; make sure the length is sufficiently large to avoid data races
        number_of_rows_per_save:
            number of rows saved at a time
        """
        BufferRing.__init__(self, buffer, length)
        SavingMixin.__init__(self, path, number_of_rows_per_save*2)
        self.number_of_rows_per_save = number_of_rows_per_save
        self.total_rows = 0
        self.last_save = 0
        self.next_save = self._compute_next_save()

    def __str__(self):
        return f"buffer: {self.shape}, position: {self.position}, total_rows: {self.total_rows}"

    def __repr__(self):
        return self.__str__()

    def add_data(self, data: int | float | np.ndarray):
        BufferRing.__init__(self, data)

        if self.saving and self.position == self.next_save:
            self.save(self.last_save, self.next_save)

        self.total_rows += 1

    def save_all(self):
        self.save(self.last_save, self.position)
        self._pause_saving = True

    def save(self, last_save: int, position: int):
        if last_save == position:
            return
        if not self._thread.is_alive():
            self._thread.start()
        if self.data_queue.full():
            raise OverflowError("Queue is not being saved fast enough. Make buffer bigger or slow down data "
                                "collection.")

        self.data_queue.put(self.get_data(last_save, position))
        self.last_save = position
        self.next_save = self._compute_next_save()

    def reset(self):
        self._resets += 1
        self.position = -1
        self.total_rows = 0
        self.last_save = 0
        self.next_save = self._compute_next_save()

    def save_and_reset(self):
        self.save_all()
        self.reset()

    def _compute_next_save(self):
        rows_left_in_ring = self.shape[0] - self.last_save
        if rows_left_in_ring < self.number_of_rows_per_save:  # loop around
            return self.number_of_rows_per_save - rows_left_in_ring
        return self.last_save + self.number_of_rows_per_save


class BufferRingTimeSavable(BufferRingSavable):
    def __init__(self,
                 path: pathlib.Path,
                 buffer: np.ndarray = None,
                 number_of_rows_per_save: int = 1000,
                 buffer_time: np.ndarray = None,
                 length: int = None
                 ):
        """

        Parameters
        ----------
        path:
            location where data will be saved.
        buffer:
            buffer; make sure the length is sufficiently large to avoid data races
        number_of_rows_per_save:
            number of rows saved at a time
        buffer_time:

        """
        super().__init__(path, buffer, number_of_rows_per_save, length=length)
        if buffer is not None:
            self.buffer_time = np.zeros(self.buffer.shape[0], dtype=np.f64)
        self.buffer_time = buffer_time

    @property
    def last_time(self) -> float:
        return self.buffer_time[self.position]

    def add_data(self, data: int | float | np.ndarray):
        BufferRing.__init__(self, data)
        self.buffer_time[self.position] = time.time()

        if self.saving and self.position == self.next_save:
            self.save(self.last_save, self.next_save)

        self.total_rows += 1

    def _create_buffer(self, data: int | float | np.ndarray):
        BufferRing.add_data(self, data)
        self.buffer_time = np.zeros(self.buffer.shape[0], dtype=np.f64)

    def get_data(self, start: int, end: int, merge: bool = True) -> tuple[np.ndarray, np.ndarray] | np.ndarray:
        if start > end:
            data = (
                np.concatenate((self.buffer_time[start:], self.buffer_time[:end])),
                np.concatenate((self.buffer[start:, :], self.buffer[0:end, :]))
                    )
        else:
            data = (
                self.buffer_time[start:end],
                self.buffer[start:end, :]
            )
        if merge:
            data = np.concatenate(data, axis=1)

        return data
