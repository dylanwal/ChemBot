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
    _DEFAULT_LENGTH = 1000

    def __init__(self, buffer: np.ndarray = None, length: int = None):
        self.buffer = buffer
        self.position = -1
        self.length = length
        self.total_rows = 0

    def __str__(self):
        return f"buffer: {self.shape}, position: {self.position}"

    def __repr__(self):
        return self.__str__()

    @property
    def shape(self) -> tuple[int, int] | None:
        if self.buffer is None:
            return None
        return self.buffer.shape

    @property
    def dtype(self):
        if self.buffer is None:
            return None
        return self.buffer.dtype

    @property
    def last_measurement(self) -> np.ndarray | None:
        if self.buffer is None:
            return None
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
                self._update_position()
                self.buffer[self.position, :] = data
            else:
                raise e

        self.total_rows += 1

    def _update_position(self):
        if self.position == self.buffer.shape[0] - 1:
            self.position = 0
        else:
            self.position += 1

    def _create_buffer(self, data: int | float | np.ndarray):
        if self.length is not None:
            length = self.length
        else:
            length = self._DEFAULT_LENGTH

        if isinstance(data, int):
            self.buffer = np.zeros((length, 1), dtype=np.int64)
        elif isinstance(data, float):
            self.buffer = np.zeros((length, 1), dtype=np.float64)
        elif isinstance(data, np.ndarray):
            self.buffer = np.zeros((length, data.shape[0]), dtype=data.dtype)
        else:
            raise TypeError(f"Invalid type.\t\nGive: {data}\t\nExpected: int | float | np.ndarray\n")

    def _get_data_index(self, start: int = None, end: int = None):
        if self.buffer is None or self.total_rows == 0:
            return None

        if start is None and end is None:
            if self.total_rows < self.buffer.shape[0]:
                start = 0
                end = self.position
            else:
                start = self.position + 1
                end = self.position + 1

        return start, end

    def get_data(self, start: int = None, end: int = None) -> np.ndarray | None:
        start, end = self._get_data_index(start, end)

        if start >= end:
            return np.concatenate((self.buffer[start:, :], self.buffer[0:end, :]))
        return self.buffer[start:end, :]

    def reset(self):
        self.position = -1
        self.total_rows = 0


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
        super().add_data(data)
        self.buffer_time[self.position] = time.time()

    def _create_buffer(self, data: int | float | np.ndarray):
        super()._create_buffer(data)
        self.buffer_time = np.zeros(self.buffer.shape[0], dtype=np.float64)

    def get_data(self, start: int = None, end: int = None, merge: bool = True) \
            -> tuple[np.ndarray, np.ndarray] | np.ndarray | None:
        start, end = self._get_data_index(start, end)

        if start >= end:
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
            data = np.column_stack(data)

        return data


class SavingMixin(abc.ABC):
    _FILE_SIZE_LIMIT = 30_000

    def __init__(self, path: str | pathlib.Path, queue_size: int, saving: bool = True):
        self._path = None
        self.path = path

        # stuff for saving via thread
        self.saving = saving
        self._data_queue = queue.Queue(maxsize=queue_size)

        self._file_counter = 0
        self._resets = 0
        self._reset_saving = False
        self._thread = threading.Thread(target=self._thread_save)
        self._thread.start()

    @property
    def path(self) -> pathlib.Path | None:
        return self._path

    @path.setter
    def path(self, path: str | pathlib.Path):
        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path)
        if not path.suffix == ".csv":
            path = path.with_suffix(".csv")
        self._path = path

    def get_file_path(self, index: int) -> pathlib.Path:
        path = self.path
        if self._resets > 0:
            path = path.with_stem(path.stem + "_reset" + str(self._resets))
        if index > 0:
            path = path.with_stem(path.stem + "_" + str(index))

        # check for issue accessing the file
        if os.path.isfile(path) and not os.access(path, os.W_OK):
            logger.warning(path)
            logger.warning(os.access(path, os.W_OK))
            path = path.with_stem(path.stem + "_new")

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
            file_path = self.get_file_path(index)
            with open(file_path, mode="w", encoding="utf-8") as f:
                while True:
                    try:
                        range_ = self._data_queue.get(timeout=0.2)  # blocking
                    except queue.Empty:
                        if not main_thread.is_alive():
                            if close_thread:
                                break
                            self.save_all()
                            close_thread = True
                            continue
                        if self._reset_saving:
                            # move onto next file
                            self._reset_saving = False
                            break

                        # continue waiting for data to come into queue
                        continue

                    ########################################################
                    # data has come in for saving
                    data: np.ndarray | None = self.get_data(*range_)
                    if data is None:
                        continue
                    for row in data:
                        f.write(','.join(str(i) for i in row))
                        f.write('\n')

                    # check if we have hit row limit for current file
                    counter += data.shape[0]
                    if counter > self._FILE_SIZE_LIMIT:
                        break

            if counter == 0:
                try:
                    os.remove(file_path)
                except PermissionError:
                    logger.warning(f"couldn't delete blank file: {file_path}. This could be because it was already "
                                   f"deleted by another thread; which means there could be two threads saving to the "
                                   f"same path. Double check that buffers are saving to different paths.")
                    # blank file doesn't get deleted

    @abc.abstractmethod
    def save_all(self):
        ...

    @abc.abstractmethod
    def get_data(self, start: int = None, end: int = None) -> np.ndarray | None:
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
    _NUMBER_OF_ROWS_PER_SAVE_DEFAULT = 1000
    _SAVING_TIMEOUT = 3  # seconds

    def __init__(self,
                 path: pathlib.Path,
                 buffer: np.ndarray = None,
                 number_of_rows_per_save: int = None,
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
        SavingMixin.__init__(self, path, 2)
        self.number_of_rows_per_save = number_of_rows_per_save
        self._last_save = 0
        self._next_save = None

    def add_data(self, data: int | float | np.ndarray):
        BufferRing.add_data(self, data)

        if self.saving and self.position == self._next_save:
            self.save(self._last_save, self.position + 1)  # +1 is for non-exclusive

        self.total_rows += 1

    def save_all(self):
        self.save(self._last_save, self.position + 1)  # +1 is for non-exclusive
        self.reset()

    def save(self, last_save: int, position: int):
        if last_save == position or position == -1:
            return
        if self._data_queue.full():
            raise OverflowError("Queue is not being saved fast enough. Make buffer bigger or slow down data "
                                "collection.")
        self._data_queue.put((last_save, position))
        self._last_save = position
        self._next_save = self._compute_next_save()

    def _get_number_of_rows_per_save(self):
        if self.number_of_rows_per_save is None:
            self.number_of_rows_per_save = min(self._NUMBER_OF_ROWS_PER_SAVE_DEFAULT, int(self.buffer.shape[0] / 2) - 1)

    def _create_buffer(self, data: int | float | np.ndarray):
        BufferRing._create_buffer(self, data)
        self._get_number_of_rows_per_save()
        self._next_save = self._compute_next_save()

    def reset(self):
        time_out = time.time() + self._SAVING_TIMEOUT
        while time.time() < time_out:
            if self._data_queue.empty():
                time.sleep(0.1)
                self._reset_saving = True
                BufferRing.reset(self)
                self._resets += 1
                self._last_save = 0
                self._next_save = self._compute_next_save()
                return
            else:
                time.sleep(0.1)

        raise TimeoutError("Queue never emptied out, so reset can't happened.")

    def _compute_next_save(self):
        rows_left_in_ring = self.shape[0] - self._last_save
        if rows_left_in_ring < self.number_of_rows_per_save:  # loop around
            return self.number_of_rows_per_save - 1 - rows_left_in_ring
        return self._last_save - 1 + self.number_of_rows_per_save


class BufferRingTimeSavable(BufferRingSavable):
    def __init__(self,
                 path: pathlib.Path,
                 buffer: np.ndarray = None,
                 number_of_rows_per_save: int = None,
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
            self.buffer_time = np.zeros(self.buffer.shape[0], dtype=np.float64)
        self.buffer_time = buffer_time

    @property
    def last_time(self) -> float:
        return self.buffer_time[self.position]

    def add_data(self, data: int | float | np.ndarray):
        BufferRing.add_data(self, data)
        self.buffer_time[self.position] = time.time()

        if self.saving and self.position == self._next_save:
            self.save(self._last_save, self._next_save + 1)  # +1 is for non-exclusive

        self.total_rows += 1

    def _create_buffer(self, data: int | float | np.ndarray):
        BufferRingSavable._create_buffer(self, data)
        self.buffer_time = np.zeros(self.buffer.shape[0], dtype=np.float64)

    def get_data(self, start: int = None, end: int = None, merge: bool = True) \
            -> tuple[np.ndarray, np.ndarray] | np.ndarray | None:
        start, end = self._get_data_index(start, end)

        if start >= end:
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
            data = np.column_stack(data)

        return data
