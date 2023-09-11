import enum

import numpy as np

import plotly.graph_objs as go
from plotly.subplots import make_subplots

from scipy import sparse
from scipy.sparse.linalg import spsolve

from typing import Annotated, Literal, TypeVar, Callable
import numpy.typing as npt

DType = TypeVar("DType", bound=np.generic)

array_int16_nx2 = Annotated[npt.NDArray[np.int16], Literal["n", 2]]
array_bool_n = Annotated[bool, Literal["n"]]


def exponatial_filter(data: np.ndarray, a: float = 0.9):
    data = np.copy(data)
    for row in range(1, len(data)):
        data[row, 1:] = a * data[row - 1, 1:] + (1 - a) * data[row, 1:]
    return data


def adaptive_polynomial_baseline(
        x: np.ndarray,
        y: np.ndarray,
        remove_amount: float = 0.4,
        deg: int = 0,
        num_iter: int = 5) \
        -> tuple[np.ndarray, np.ndarray]:
    """ Adaptive polynomial baseline correction

    The algorithm:
    1) calculate fit to the data
    2) removes some percent of data points furthest from the fit
    3) calculate a new fit from this 'masked data'
    4) starting with the raw data, removes some percent of data points (a larger percent then the first time) furthest
    from the fit
    5) repeat steps 3-4

    Parameters
    ----------
    x: np.ndarray[:]
        x data
    y: np.ndarray[:]
        y data
    remove_amount: float
        range: (0-1)
        amount of data to be removed by the end of all iterations
    deg: int
        range: [0, 10]
        degree of polynomial
    num_iter: int
        range: [2, +]
        number of iteration

    Returns
    -------

    """
    if num_iter < 1:
        raise ValueError("'num_iter' must be larger than 1.")

    x_mask = x
    y_mask = y
    number_of_points_to_remove_each_iteration = int(len(x) * remove_amount / num_iter)
    for i in range(num_iter):
        # perform fit
        params = np.polyfit(x_mask, y_mask, deg)
        func_baseline = np.poly1d(params)
        y_baseline = func_baseline(x)

        if i != num_iter:  # skip on last iteration
            # get values furthest from the baseline
            number_of_points_to_remove = number_of_points_to_remove_each_iteration * (i + 1)
            index_of_points_to_remove = np.argsort(np.abs(y - y_baseline))[-number_of_points_to_remove:]
            y_mask = np.delete(y, index_of_points_to_remove)
            x_mask = np.delete(x, index_of_points_to_remove)

    y = y - y_baseline

    return x, y


def baseline_als(x: np.ndarray, y: np.ndarray, lam: float = 1_000, p: float = 0.01, niter=10):
    """Asymmetric Least Squares Smoothing """
    L = len(y)
    D = sparse.diags([1, -2, 1], [0, -1, -2], shape=(L, L - 2))
    w = np.ones(L)
    for i in range(niter):
        W = sparse.spdiags(w, 0, L, L)
        Z = W + lam * D.dot(D.transpose())
        z = spsolve(Z, w * y)
        w = p * (y > z) + (1 - p) * (y < z)
    return x, z


def canny_edge_detector_1d(data, low_threshold, high_threshold):
    # Apply Gaussian blur to reduce noise (optional for 1D data)
    blurred_data = np.convolve(data, np.ones(5) / 5, mode='same')

    # Calculate the gradient magnitude using central differences
    gradient = np.gradient(blurred_data)

    # Calculate the magnitude of the gradient
    gradient_magnitude = np.abs(gradient)

    # Non-maximum suppression
    edges = np.zeros_like(gradient_magnitude)
    for i in range(1, len(edges) - 1):
        if gradient_magnitude[i] > gradient_magnitude[i - 1] and gradient_magnitude[i] > gradient_magnitude[i + 1]:
            edges[i] = gradient_magnitude[i]

    # Apply thresholding to find strong edges
    edges = (edges > high_threshold) * edges

    return edges


def convert_to_binary(array, threshold):
    binary_array = np.where(array > threshold, 1, 0)
    return binary_array


class Slug:
    sensor_spacer = 0.95  # cm
    __slots__ = ("time_start_1", "time_end_1", "time_start_2", "time_end_2", "_length", "_velocity")

    def __init__(self,
                 time_start_1: float | int,
                 time_end_1: float | int = None,
                 time_start_2: float | int = None,
                 time_end_2: float | int = None
                 ):
        self.time_start_1 = time_start_1
        self.time_end_1 = time_end_1
        self.time_start_2 = time_start_2
        self.time_end_2 = time_end_2
        self._length = None
        self._velocity = None

    def __str__(self):
        if not self.is_complete:
            text = f"slug_start: ({self.time_start_1}, {self.time_start_2}); No end detected"
        else:
            text = f"vel:{self.velocity:03.02}, len: {self.length:03.02}"
        return text

    @property
    def is_complete(self) -> bool:
        return not (self.time_end_1 is None or self.time_end_2 is None or self.time_start_2 is None)

    @property
    def velocity(self) -> float | None:
        if self._velocity is None:
            if not self.is_complete:
                return None
            self._velocity = self.sensor_spacer / \
                             ((self.time_start_2 - self.time_start_1 + self.time_end_2 - self.time_end_1) / 2)

        return self._velocity

    @property
    def length(self) -> float | None:
        if self._length is None:
            if self.velocity is None:
                return None
            self._length = self.velocity * (self.time_end_1 - self.time_start_1 + self.time_end_2 - self.time_start_2)/2

        return self._length


def extract_transitions(data: array_bool_n):
    # Find transitions from 0 to 1 (0 -> 1)
    shifted_states = np.roll(data, 1)
    ups = (data == 1) & (shifted_states == 0)  # puts True on first True after rise
    # Find transitions from 1 to 0 (1 -> 0)
    downs = (data == 0) & (shifted_states == 1)  # puts True on first False after dip

    return np.where(ups | downs)[0]  # index of transitions


def edges_to_slugs(data: np.ndarray) -> list[Slug]:
    # index = np.concatenate((extract_transitions(data[:, 1]), extract_transitions(data[:, 2])))
    # index.sort()
    # index = np.concatenate((index, index - 1, index + 1))
    # index.sort()
    # data = data[index, :]

    slugs = []
    slug_buffer = None
    slug_buffer2 = None
    for i in range(1, data.shape[0]):
        if data[i, 1] - data[i - 1, 1] == 1:
            if slug_buffer is not None:
                if slug_buffer2 is None:
                    slug_buffer2 = slug_buffer
                else:
                    slugs.append(slug_buffer2)  # not complete

            slug_buffer = Slug(data[i, 0])

        elif data[i, 1] - data[i - 1, 1] == -1:
            if slug_buffer is None:
                continue
            slug_buffer.time_end_1 = data[i, 0]
        elif data[i, 2] - data[i - 1, 2] == 1:
            if slug_buffer is None:
                continue
            slug_buffer.time_start_2 = data[i, 0]
        elif data[i, 2] - data[i - 1, 2] == -1:
            if slug_buffer is None:
                continue
            if slug_buffer2 is not None:
                slug_buffer2.time_end_2 = data[i, 0]
                slugs.append(slug_buffer2)
                slug_buffer2 = None
            else:
                slug_buffer.time_end_2 = data[i, 0]
                slugs.append(slug_buffer)
                slug_buffer = None

    if slug_buffer is not None:
        slugs.append(slug_buffer)
    if slug_buffer2 is not None:
        slugs.append(slug_buffer2)

    return slugs


def print_slug_data(slugs: list[Slug]):
    for i, slug in enumerate(slugs):
        print(i, slug)

    print()
    print("avg. velocity: ", np.mean([slug.velocity for slug in slugs]))
    print("avg. length: ", np.mean([slug.length for slug in slugs]))


def main():
    data = np.genfromtxt("data_0.csv", delimiter=",")
    data[:, 0] = data[:, 0] - data[0, 0]

    # exponential
    data_proc = exponatial_filter(data, 0.9)

    data_proc[:, 1] = convert_to_binary(data_proc[:, 1],
                                        (np.max(data_proc[:, 1]) - np.min(data_proc[:, 1])) / 2 + np.min(
                                            data_proc[:, 1]))
    data_proc[:, 2] = convert_to_binary(data_proc[:, 2],
                                        (np.max(data_proc[:, 2]) - np.min(data_proc[:, 2])) / 2 + np.min(
                                            data_proc[:, 2]))

    # slugs = edges_to_slugs(data_proc)
    # print_slug_data(slugs)

    # figure
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=data[:, 0], y=data[:, 1], mode="lines"))
    fig.add_trace(go.Scatter(x=data[:, 0], y=data[:, 2], mode="lines"))
    fig.add_trace(
        go.Scatter(x=data_proc[:, 0], y=data_proc[:, 1], mode="lines", legendgroup="process"),
                  secondary_y=True
    )
    fig.add_trace(go.Scatter(x=data_proc[:, 0], y=data_proc[:, 2], mode="lines",
                             legendgroup="process"), secondary_y=True)
    fig.write_html("temp.html", auto_open=True)


class RingBufferSimple:
    def __init__(self, buffer: np.ndarray):
        self._buffer = buffer
        self.position = 0

    @property
    def buffer(self) -> np.ndarray:
        return self._buffer

    def add_data(self, data: int | float | np.ndarray):
        if self.position == self._buffer.shape[0] - 1:
            self.position = 0
        else:
            self.position += 1

        self._buffer[self.position, :] = data


class CUSUM:
    class States(enum.Enum):
        init = 0
        down = 1
        up = 2

    def __init__(self, c_limit: float | int = 1, n: int = 10, filter_: Callable = None):
        """
        Parameters
        ----------
        c_limit:
            Control limit, specified as a real scalar expressed in standard deviations.
        n:
            number points to calculate standard_deviation and mean
        filter_
        """
        self.filter_ = filter_
        self.n = n
        self.c_limit = c_limit

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
            if isinstance(data, np.ndarray):
                self._data = RingBufferSimple(np.zeros((self.n, len(data))))
            else:
                self._data = RingBufferSimple(np.zeros((self.n, 1)))
            self._data.add_data(data)

        self._mean = np.mean(self._data.buffer)
        self._standard_deviation = np.std(self._data.buffer)

        self._up_sum = np.max((0, self._up_sum + data - self._mean - 1/2*3*self._standard_deviation))
        self._low_sum = np.min((0, self._low_sum + data - self._mean + 1/2*3*self._standard_deviation))

        if self._count > self.n:
            if self._up_sum > self.c_limit*self._standard_deviation:
                self._state = self.States.up
            if self._low_sum < - self.c_limit * self._standard_deviation:
                self._state = self.States.down
            if self._state != self._prior_state:
                return self.state

        return None  # no event detected


def main2():
    data = np.genfromtxt("data_0.csv", delimiter=",")
    data[:, 0] = data[:, 0] - data[0, 0]
    # data_proc = exponatial_filter(data, 0.8)

    # exponential
    algorithm = CUSUM()
    state = np.zeros(data.shape[0], dtype=np.int8)
    up = np.zeros(data.shape[0])
    down = np.zeros(data.shape[0])
    for i in range(data.shape[0]):
        new_data_point = data[i, 1]
        event = algorithm.add_data(new_data_point)
        up[i] = algorithm._up_sum
        down[i] = algorithm._low_sum
        if event:
            state[i] = event.value
    # slugs = cumulative_sum_control(data_proc)
    # print_slug_data(slugs)

    # figure
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=data[:, 0], y=data[:, 1], mode="lines"))
    # fig.add_trace(go.Scatter(x=data[:, 0], y=data[:, 2], mode="lines"))
    fig.add_trace(
        go.Scatter(x=data[:, 0], y=up, mode="lines", legendgroup="process"),
                  secondary_y=True
    )
    fig.add_trace(
        go.Scatter(x=data[:, 0], y=down, mode="lines", legendgroup="process"),
                  secondary_y=True
    )

    fig.write_html("temp.html", auto_open=True)


if __name__ == "__main__":
    main2()


