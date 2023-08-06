from typing import Protocol

import numpy as np


class Buffer(Protocol):
    dtype = None
    shape: tuple[int, int]
    save_data: bool

    def add_data(self, data: int | float | np.ndarray):
        ...

    def save(self, last_save: int, next_save: int):
        ...

    def save_all(self):
        ...

    def reset(self):
        ...

    def save_and_reset(self):
        self.save_all()
        self.reset()

    def reshape(self, shape: tuple[int, int]):
        ...
