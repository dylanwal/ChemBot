import pathlib
import queue
import sys
import threading
import time

import numpy as np

from chembot.configuration import config


class BufferRing:
    """
    The buffer ring is an efficient way to reuse the same memory over and over  again for data streaming in.
    It will periodically save data to a csv for long term storage.

    threading is used to ensure data can still be added while the save is happening.
    Note that data is saved from the buffer at the same time data is being written to it 'creating a data race'.
    This is not a problem if the buffer is big enough to not be reading and writing to the same cell at the same
    time. A check is added to stop if buffer is overfilled.

    """
    _file_size_limit = 30_000

    def __init__(self,
                 path: pathlib.Path,
                 dtype,
                 buffer_shape: tuple[int, int] = (10_000, 8),
                 number_of_rows_per_save: int = 1000,
                 save_data: bool = True
                 ):
        """

        Parameters
        ----------
        path:
            location where data will be saved.
        dtype:
            dtype for numpy array
        buffer_shape:
            buffer size; make sure the length is sufficiently large to avoid data races
        number_of_rows_per_save:
            number of rows saved at a time
        save_data:
            save data periodical to csv as the buffer fills up
        """
        self._buffer = np.empty(buffer_shape, dtype=dtype)
        self.number_of_rows_per_save = number_of_rows_per_save
        self.position = -1
        self.total_rows = 0

        self._next_save = self.number_of_rows_per_save - 1
        self._last_save = 0
        self._resets = 0

        # stuff for saving via thread
        self.save_data = save_data
        if path.suffix:
            path = path.parent / path.stem
        else:
            path = path / "data"
        self.path = path
        self.data_queue = queue.Queue(maxsize=int(buffer_shape[0]/number_of_rows_per_save)-1)
        self.save_thread = threading.Thread(target=self._thread_save)
        self._done = False
        if self.save_data:
            self.save_thread.start()

    def __str__(self):
        return f"buffer: {self.shape}, position: {self.position}, total_rows: {self.total_rows}"

    def __repr__(self):
        return self.__str__()

    @property
    def shape(self) -> tuple[int, int]:
        return self._buffer.shape

    @property
    def dtype(self):
        return self._buffer.dtype

    def reshape(self, shape: tuple[int, int]):
        """ reshaping clears buffer """
        self._buffer = np.empty(shape, dtype=self.dtype)

    def get_file_path(self, index: int) -> pathlib.Path:
        path = self.path
        if self._resets > 0:
            path.stem += "_r" + str(self._resets)
        path = path.with_stem(path.stem + "_" + str(index))
        path = path.with_suffix(".csv")
        return path

    def _compute_next_save(self):
        rows_left_in_ring = self.shape[0] - self._last_save
        if rows_left_in_ring < self.number_of_rows_per_save:
            # loop around
            return self.number_of_rows_per_save - rows_left_in_ring

        return self._last_save + self.number_of_rows_per_save

    def add_data(self, data: int | float | np.ndarray):
        if self.position == self._buffer.shape[0] - 1:
            self.position = 0
        else:
            self.position += 1

        self._buffer[self.position, :] = data

        # Check if saving is necessary
        if self.save_data and self.position == self._next_save:
            self.save(self._last_save, self._next_save)

        self.total_rows += 1

    def save_all(self):
        self.save(self._last_save, self.position)

    def save(self, last_save: int, next_save: int):
        if not self.save_thread.is_alive():
            self.save_thread.start()

        if last_save > next_save:
            data = np.concatenate((
                self._buffer[last_save:, :],
                self._buffer[0:next_save, :]
            ))
        else:
            data = self._buffer[last_save:next_save, :]

        if self.data_queue.full():
            raise OverflowError("Queue is not being saved fast enough. Make buffer bigger or slow down data "
                                "collection.")
        self.data_queue.put(data)
        self._last_save = next_save
        self._next_save = self._compute_next_save()

    def reset(self):
        self._resets += 1
        self.position = 0
        self.total_rows = 0
        self._last_save = 0
        self._next_save = self.number_of_rows_per_save - 1

    def save_and_reset(self):
        self.save(self._last_save, self.position)
        self.reset()

    def _thread_save(self):
        """
        this function periodically saves data from the buffer to csv.
        this function is called by the thread.
        """
        main_thread = threading.main_thread()
        index = -1
        while True:
            index += 1  # counter for index path name for each new file
            counter = 0  # counter when to start a new file
            with open(self.get_file_path(index), mode="w", encoding=config.encoding) as f:
                while True:
                    try:
                        data: np.ndarray = self.data_queue.get(timeout=1)  # blocking
                    except queue.Empty:
                        # check to make sure main thread is still running
                        if main_thread.is_alive():
                            continue
                        # if main thread done; save everything
                        if not self._done:
                            self.save_all()
                            self._done = True
                        else:  # exit once everything is saved close thread
                            sys.exit()

                    # write row
                    for row in data:
                        f.write(','.join(str(i) for i in row))
                        f.write('\n')

                    # check if we have hit row limit for current file
                    counter += data.shape[0]
                    if counter > self._file_size_limit:
                        break


class BufferRingTime(BufferRing):
    def __init__(self,
                 path: pathlib.Path,
                 dtype,
                 buffer_shape: tuple[int, int] = (10_000, 8),
                 number_of_rows_per_save: int = 1000,
                 save_data: bool = True
                 ):
        """

        Parameters
        ----------
        path:
            location where data will be saved.
        dtype:
            dtype for numpy array
        buffer_shape:
            buffer size; make sure the length is sufficiently large to avoid data races
        number_of_rows_per_save:
            number of rows saved at a time
        save_data:
            save data periodical to csv as the buffer fills up
        """
        super().__init__(path, dtype, buffer_shape, number_of_rows_per_save, save_data)
        self.time = time.time()

    def add_data(self, data: int | float | np.ndarray):
        if self.position == self._buffer.shape[0] - 1:
            self.position = 0
        else:
            self.position += 1
        self.time = time.time()
        super().add_data(data)

    def save(self, last_save: int, next_save: int):
        if not self.save_thread.is_alive():
            self.save_thread.start()

        if last_save > next_save:
            data = np.concatenate((
                self._buffer[last_save:, :],
                self._buffer[0:next_save, :]
            ))
        else:
            data = self._buffer[last_save:next_save, :]

        # add time row
        data = np.column_stack((self.time[last_save:next_save], data))

        if self.data_queue.full():
            raise OverflowError("Queue is not being saved fast enough. Make buffer bigger or slow down data "
                                "collection.")
        self.data_queue.put(data)
        self._last_save = next_save
        self._next_save = self._compute_next_save()
