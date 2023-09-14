import numpy as np
from typing import Sized


def get_max_index(index: int | slice | tuple[int]) -> int:
    """ get max index """
    if isinstance(index, int):
        return abs(index)
    if isinstance(index, tuple):
        return abs(int(index[0]))

    # index must be a slice
    return abs(int(index.stop))


def get_object_size(x: int | float | Sized) -> int:
    if isinstance(x, int) or isinstance(x, float):
        return 1
    if isinstance(x, np.ndarray):
        return x.shape[0]
    elif hasattr(x, "__len__"):
        return len(x)
    else:
        raise ValueError("Invalid item to add.")


class DynamicArray:
    """
    A class to dynamically grow numpy array as data is added in an efficient manner.
    For arrays or column vectors (new rows added, but no new added columns).

    Attributes:
    ----------
    shape: int, array_type
        Starting shape of the dynamic array
    index_expansion: bool
        allow setting indexing outside current capacity
        will set all values between previous size to new value to zero

    Example
    -------
    a = DynamicArray((100, 2))
    a.append(np.ones((20, 2)))
    a.append(np.ones((120, 2)))
    a.append(np.ones((10020, 2)))
    print(a.data)
    print(a.data.shape)
    """

    def __init__(self, shape: tuple[int, int] | int = (100,), index_expansion: bool = False):
        self._data = None
        self.capacity = shape[0]
        self.size = 0
        self.index_expansion = index_expansion

    def __str__(self):
        return self.data.__str__()

    def __repr__(self):
        return self.data.__repr__().replace("array", f'DynamicArray(size={self.size}, capacity={self.capacity})')

    def __getitem__(self, index: int | slice | tuple[int]):
        size = get_max_index(index)
        if size > self.size:
            raise IndexError(f"index {size} is out of bounds for axis 0 with size {self.size}")

        return self.data[index]

    # def __setitem__(self, index: int | slice | tuple[int], value: int | slice | tuple[int]):
    #     max_index = get_max_index(index)
    #     if max_index > self.size and not self.index_expansion:
    #         raise IndexError(f"index {max_index} is out of bounds for axis 0 with size {self.size}")
    #
    #     size = get_object_size(x)
    #     self._capacity_check(size)
    #
    #     # add data
    #     if isinstance(index, int) and index < 0 or \
    #             isinstance(index, slice) and (index.start < 0 or index.stop < 0) or \
    #             isinstance(index, tuple) and any(i < 0 for i in index):
    #         # handle negative indexing
    #         self.data[index] = value
    #     else:
    #         # handling positive indexing
    #         self._data[index] = value
    #
    #     # update capacity and size (if it was outside current size)
    #     if max_index > self.size:
    #         capacity_change = max_index - self.size
    #         self.capacity -= capacity_change
    #         self.size += capacity_change

    def __getattribute__(self, name):
        try:
            attr = object.__getattribute__(self, name)
        except AttributeError:
            # check numpy for function call
            attr = object.__getattribute__(self.data, name)

        if hasattr(attr, '__call__'):
            def newfunc(*args, **kwargs):
                result = attr(*args, **kwargs)
                return result
            return newfunc

        else:
            return attr

    def __len__(self):
        return self.size

    @property
    def data(self):
        """ Returns data without extra spaces. """
        return self._data[:self.size]

    @property
    def shape(self) -> tuple[int, int]:
        return self.size, self.data.shape[0]

    @property
    def dtype(self):
        return self.data.dtype

    def append(self, x: np.ndarray | list | tuple | int | float):
        """ Add data to array. """
        size = get_object_size(x)
        self._capacity_check(size)

        # Add new data to array
        self._data[self.size:self.size + size] = x
        self.size += size
        self.capacity -= size

    def _capacity_check_index(self, index: int = 0):
        if index > len(self._data):
            add_size = (index-len(self._data)) + self.capacity
            self._grow_capacity(add_size)

    def _capacity_check(self, size: int):
        """ Check if there is room for the new data. """
        if size < self.capacity:
            return

        # calculate what change is needed.
        change_need = size - self.capacity

        # make new larger data array
        shape_ = list(self._data.shape)
        if shape_[0] + self.capacity > size:
            # double in size
            self.capacity += shape_[0]
            shape_[0] = shape_[0] * 2
        else:
            # if doubling is not enough, grow to fit incoming data exactly.
            self.capacity += change_need
            shape_[0] = shape_[0] + change_need
        newdata = np.zeros(shape_, dtype=self._data.dtype)

        # copy data into new array and replace old one
        newdata[:self._data.shape[0]] = self._data
        self._data = newdata
