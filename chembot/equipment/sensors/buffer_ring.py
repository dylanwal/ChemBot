import pathlib

import threading
import numpy as np


def save_data(file_path: pathlib.Path, data: np.ndarray):


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
        self.window_size = window_size
        self.lag = lag
        self.position = -1
        self.total_rows = 0

        self.lock = threading.Lock()
        self._next_save = None
        self._compute_first_save()
        self._resets = 0

    @property
    def window_index(self) -> tuple[int, int]:
        tail = self.position - self.window_size if self.position - self.window_size else 0
        return tail, self.position

    @property
    def window_

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
        if self.position == self._next_save:
            self.save()

        self.total_rows += 1

    def save(self):
        save_thread = threading.Thread(target=save_data, args=(self.file_path, self.buffer))
        save_thread.start()
        self._compute_next_save()

    def reset(self):
        self._resets += 1
        self.position = 0
        self.total_rows = 0
        self._compute_first_save()

    def save_reset(self):
        self.save()
        self.reset()