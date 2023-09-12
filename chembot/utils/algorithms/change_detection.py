import enum

import numpy as np

from chembot.utils.buffers.buffer_ring import BufferRing


class CUSUM:
    """
    The CUSUM control chart is designed to detect small incremental changes in the mean of a process.
    https://www.mathworks.com/help/signal/ref/cusum.html

    """
    class States(enum.Enum):
        init = 0
        down = 1
        up = 2

    def __init__(self, c_limit: float | int = 3, n: int = 31, sigma: int | float = 3):
        """
        Parameters
        ----------
        c_limit:
            Control limit, is the number of standard deviations from the mean that will be accepted as an event
        n:
            number points to calculate standard_deviation and mean
        sigma:
            Minimum mean shift to detect; is the number of standard deviations from the mean that make a
            shift detectable.
        """
        self.c_limit = c_limit
        self.n = n
        self.sigma = sigma

        self._state = self.States.init
        self._prior_state = self.States.init
        self._up_sum = 0
        self._low_sum = 0
        self._mean = 0
        self._standard_deviation = 0
        self._data = None
        self._count = 0

    @property
    def state(self) -> States:
        return self._state

    def add_data(self, data: np.ndarray) -> States | None:
        self._count += 1
        try:  # try loop used for performance
            self._data.add_data(data)
        except AttributeError:
            self._data = BufferRing()
            self._data.add_data(data)

        self._mean = np.mean(self._data.buffer)
        self._standard_deviation = np.std(self._data.buffer)

        self._up_sum = np.max((0, self._up_sum + data - self._mean - 1/2*self.sigma*self._standard_deviation))
        self._low_sum = np.min((0, self._low_sum + data - self._mean + 1/2*self.sigma*self._standard_deviation))

        if self._count > self.n:
            if self._up_sum > self.c_limit*self._standard_deviation:
                self._state = self.States.up
            if self._low_sum < - self.c_limit * self._standard_deviation:
                self._state = self.States.down
            if self._state != self._prior_state:
                return self.state

        return None  # no event detected
