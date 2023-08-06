import numpy as np
import plotly.graph_objs as go
from scipy import sparse
from scipy.sparse.linalg import spsolve
from plotly.subplots import make_subplots

from typing import Annotated, Literal, TypeVar
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
    sensor_spacer = 0.95
    __slots__ = ("time_start_1", "time_end_1", "time_start_2", "time_end_2", "_volume", "_velocity")

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
        self._volume = None
        self._velocity = None

    def __str__(self):
        if self.is_complete:
            text = f"slug_start: ({self.time_start_1}, {self.time_start_2}); No end detected"
        else:
            text = f"vel:{self.velocity}, len: {self.length}"
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
                             ((self.time_end_1 - self.time_start_1 + self.time_end_2 - self.time_start_2) / 2)

        return self._velocity

    @property
    def length(self) -> float | None:
        if self._volume is None:
            if self.velocity is None:
                return None
            self._volume = self.velocity * (self.time_end_1 - self.time_end_1)

        return self._volume


def extract_transitions(data: array_bool_n):
    # Find transitions from 0 to 1 (0 -> 1)
    shifted_states = np.roll(data, 1)
    ups = (data == 1) & (shifted_states == 0)  # puts True on first True after rise
    # Find transitions from 1 to 0 (1 -> 0)
    downs = (data == 0) & (shifted_states == 1)  # puts True on first False after dip

    return np.where(ups | downs)[0]  # index of transitions


def edges_to_slugs_reduced(data: np.ndarray) -> list[Slug]:
    # reduce data to transitions
    data = data[np.concatenate((extract_transitions(data[:, 1]), extract_transitions(data[:, 2]))), :]

    slugs = []
    slug_buffer = None
    slug_buffer2 = None
    for i in range(1, data.shape[0]):
        if data[i, 1] == 1:
            if slug_buffer is not None:
                if slug_buffer2 is None:
                    slug_buffer2 = slug_buffer
                else:
                    slugs.append(slug_buffer2)  # not complete

            slug_buffer = Slug(time_start_1=data[i, 0])

        elif data[i, 1] == 0:
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


def edges_to_slugs(data: np.ndarray) -> list[Slug]:
    index = np.concatenate((extract_transitions(data[:, 1]), extract_transitions(data[:, 2])))
    index.sort()
    index = np.concatenate((index, index - 1, index + 1))
    index.sort()
    data = data[index, :]

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
    data_proc = exponatial_filter(data, 0.95)
    data_proc[:, 1] = convert_to_binary(data_proc[:, 1],
                                        (np.max(data_proc[:, 1]) - np.min(data_proc[:, 1])) / 2 + np.min(
                                            data_proc[:, 1]))
    data_proc[:, 2] = convert_to_binary(data_proc[:, 2],
                                        (np.max(data_proc[:, 2]) - np.min(data_proc[:, 2])) / 2 + np.min(
                                            data_proc[:, 2]))

    slugs = edges_to_slugs(data_proc)
    print_slug_data(slugs)

    # figure
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=data[:, 0], y=data[:, 1], mode="lines", legendgroup="raw"))
    fig.add_trace(go.Scatter(x=data[:, 0], y=data[:, 2], mode="lines", legendgroup="raw"))
    fig.add_trace(go.Scatter(x=data_proc[:, 0], y=data_proc[:, 1], mode="lines",
                             legendgroup="process"), secondary_y=True)
    fig.add_trace(go.Scatter(x=data_proc[:, 0], y=data_proc[:, 2], mode="lines",
                             legendgroup="process"), secondary_y=True)
    fig.show()


if __name__ == "__main__":
    main()
