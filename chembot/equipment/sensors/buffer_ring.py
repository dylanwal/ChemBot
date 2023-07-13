import pathlib
import queue
import threading

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
                 dtype: str,
                 buffer_shape: tuple[int, int] = (10_000, 8),
                 number_of_rows_per_save: int = 1000
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
        """
        self._buffer = np.empty(buffer_shape, dtype=dtype)
        self.number_of_rows_per_save = number_of_rows_per_save
        self.position = -1
        self.total_rows = 0

        self._next_save = self.number_of_rows_per_save - 1
        self._last_save = 0
        self._resets = 0

        # stuff for saving via thread
        if path.suffix:
            path = path.parent / path.stem
        else:
            path = path / "data"
        self.path = path
        self.data_queue = queue.Queue(maxsize=int(buffer_shape[0]/number_of_rows_per_save)-1)
        self.save_thread = threading.Thread(target=self._thread_save)
        self.save_thread.daemon = False  # Set the save thread as a daemon thread to automatically exit with the main
        self._done = False
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

    def get_file_path(self, index: int) -> pathlib.Path:
        path = self.path
        if self._resets > 0:
            path.stem += "_r" + str(self._resets)
        path = path.with_stem(path.stem + "_" + str(index))
        path = path.with_suffix(".csv")
        return path

    def done(self):
        self.save_all()
        self._done = True

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
        if self.position == self._next_save:
            self.save(self._last_save, self._next_save)

        self.total_rows += 1

    def save_all(self):
        self.save(self._last_save, self.position)

    def save(self, last_save: int, next_save: int):
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
        index = -1
        while True:
            index += 1  # counter for index path name for each new file
            if self._done:
                break

            counter = 0  # counter when to start a new file
            with open(self.get_file_path(index), mode="w", encoding=config.encoding) as f:
                while True:
                    try:
                        data: np.ndarray = self.data_queue.get(timeout=1)  # blocking
                    except queue.Empty:
                        if self._done and self.data_queue.empty():
                            break
                        else:
                            continue

                    for row in data:
                        f.write(','.join(str(i) for i in row))
                        f.write('\n')

                    counter += data.shape[0]
                    if counter > self._file_size_limit:
                        break
