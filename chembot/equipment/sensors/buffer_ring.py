import os
import pathlib
import queue
import threading

import numpy as np

from chembot.configuration import config


class BufferRing:
    _file_size_limit = 30_000

    def __init__(self,
                 path: pathlib.Path,
                 dtype: str,
                 buffer_shape: tuple[int, int] = (10_000, 8),
                 window_live: int = 1000,
                 window_save: int = 1000
                 ):
        """

        Parameters
        ----------
        dtype
        buffer_shape
        window
        lag
        """
        self.dtype = dtype
        self.buffer_shape = buffer_shape
        self.buffer = np.empty((buffer_shape, 4), dtype=dtype)
        self.window_live = window_live
        self.window_save = window_save
        self.position = -1
        self.total_rows = 0

        self.data_queue = queue.Queue()
        self.save_thread = threading.Thread(target=self._thread_save)
        self.save_thread.daemon = True  # Set the save thread as a daemon thread to automatically exit with the main
        self.save_thread.start()

        self._next_save = None
        self._last_save = 0
        self._compute_first_save()
        self._resets = 0

    @property
    def window_data(self) -> np.ndarray:
        if self.position - self.window_live < 0:
            return np.concatenate((
                self.buffer[-1 - (self.window_live - self.position):-1, :],
                self.buffer[0:self.position, :]
            ))

        return self.buffer[self.position - self.window_live:self.position, :]

    @property
    def save_data(self) -> np.ndarray:
        if self._last_save - self.window_live < 0:
            return np.concatenate((
                self.buffer[-1 - (self.window_live - self.position):-1, :],
                self.buffer[0:self.position, :]
            ))

        return self.buffer[self.position - self.window_live:self.position, :]

    @property
    def file_path(self) -> pathlib.Path:
        path = self.file_path
        if self._resets > 0:
            path /= str(self._resets)
        return path / str(self.total_data % self._file_size_limit)

    def _compute_first_save(self):
        self._next_save = self.lag + self.window_size

    def _compute_next_save(self):
        self._next_save += self.window_size

    def add_data(self, data: np.ndarray):
        if self.position - 1 == self.buffer.shape[0]:
            self.position = 0
        else:
            self.position =+ 1

        self.buffer[self.position] = data

        # Check if saving is necessary
        if self.position >= self._next_save:
            self.save(self._last_save, self._next_save)

        self.total_rows += 1

    def save(self, start: int, end: int):
        self.data_queue.put(self.save_data)
        self._compute_next_save()

    def reset(self):
        self._resets += 1
        self.position = 0
        self.total_rows = 0
        self._compute_first_save()

    def save_reset(self):
        self.save(self._last_save, self.position)
        self.reset()

    def _thread_save(self):
        while True:
            data: np.ndarray = self.data_queue.get()

            file_name = self.file_path
            if os.path.isfile(file_name):
                edit_type = "a"
            else:
                edit_type = "w"
            with open(file_name, mode=edit_type, encoding=config.encoding) as f:
                f.write(','.join(map(str, data)))
                f.write('\n')
