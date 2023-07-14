from typing import Protocol

import numpy as np


class Buffer(Protocol):
    dtype = None
    shape: tuple[int, int]

    def add_data(self, data: int | float | np.ndarray):
        ...

    def save(self, last_save: int, next_save: int):
        ...

    def reset(self):
        ...

    def reshape(self, shape: tuple[int, int]):
        ...