from typing import Protocol

import numpy as np


class Buffer(Protocol):
    dtype = None
    shape: tuple[int, int]
    buffer: np.ndarray
    position: int
    capacity: int

    def add_data(self, data: int | float | np.ndarray):
        ...


class BufferSavable(Buffer):
    save_data: bool

    def save(self, last_save: int, next_save: int):
        ...

    def save_all(self):
        ...

    def reset(self):
        ...

    def save_and_reset(self):
        self.save_all()
        self.reset()
