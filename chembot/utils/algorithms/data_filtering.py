
import numpy as np


class Filter:

    def __init__(self):
        pass

    def process_data(self, data):
        pass


def savitzky_golay_filter_matrix(data: np.ndarray, window_size, order, axis=0, deriv=0, rate=1):
    """
    Applies the Savitzky-Golay filter to a matrix along a specified axis.

    Parameters
    ---------
    data:
        Input matrix of data points.
    window_size:
        Size of the smoothing window. It must be a positive odd number.
    order:
        Order of the polynomial to fit. It must be a non-negative integer.
    axis:
        The axis along which to apply the filter (default: 0).
    deriv:
        The order of the derivative to compute (default: 0).
    rate:
        The sampling rate of the input data (default: 1).

    Returns
    -------
    results:
        The filtered matrix.
    """
    try:
        window_size = np.abs(int(window_size))
        order = np.abs(int(order))
    except ValueError:
        raise ValueError("window_size and order have to be of type int")

    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("window_size size must be a positive odd number")
    if window_size < order + 2:
        raise TypeError("window_size is too small for the polynomials order")

    filtered_matrix = np.apply_along_axis(
        lambda x: savitzky_golay_filter(x, window_size, order, deriv=deriv, rate=rate),
                                          axis=axis, arr=data
    )

    return filtered_matrix


def savitzky_golay_filter(y, window_size, order, deriv=0, rate=1):
    """
    Applies the Savitzky-Golay filter to a one-dimensional array.

    Args:
        y (ndarray): Input one-dimensional array of data points.
        window_size (int): Size of the smoothing window. It must be a positive odd number.
        order (int): Order of the polynomial to fit. It must be a non-negative integer.
        deriv (int, optional): The order of the derivative to compute (default: 0).
        rate (int, optional): The sampling rate of the input data (default: 1).

    Returns:
        ndarray: The filtered array.

    Raises:
        ValueError: If `window_size` or `order` is not of type int.
        TypeError: If `window_size` is not a positive odd number or if it is too small for the given order.

    """
    order_range = range(order + 1)
    half_window = (window_size - 1) // 2
    b = np.mat([[k ** i for i in order_range] for k in range(-half_window, half_window + 1)])
    m = np.linalg.pinv(b).A[deriv] * rate ** deriv * np.factorial(deriv)
    firstvals = y[0] - np.abs(y[1:half_window + 1][::-1] - y[0])
    lastvals = y[-1] + np.abs(y[-half_window - 1:-1][::-1] - y[-1])
    y = np.concatenate((firstvals, y, lastvals))
    return np.convolve(m[::-1], y, mode='valid')


def filter_exponential(prior_data: np.ndarray, new_data: np.ndarray, a: int | float = 0.8) -> np.ndarray:
    """
    The exponential filter is a weighted combination of the previous estimate (output) with the newest input data,
    with the sum of the weights equal to 1 so that the output matches the input at steady state.

    Parameters
    ----------
    prior_data:
        filtered output from last time step
    new_data:
        new data for this time step
    a:
        smoothing constant
        a is a constant between 0 and 1, normally between 0.8 and 0.99

    Returns
    -------
    result:
         filtered output for this step
    """
    return a * prior_data + (1 - a) * new_data


filter_exponential.min_number_points = 2


def filter_low_pass_fft(data: np.ndarray, cutoff_freq: int = 50, sampling_freq: int = 1000):
    """

    Parameters
    ----------
    data
    cutoff_freq
    sampling_freq

    Returns
    -------

    """
    # Calculate the normalized cutoff frequency
    normalized_cutoff_freq = cutoff_freq / (0.5 * sampling_freq)

    # Perform the Fourier transform
    fft = np.fft.fft(data)

    # Create the frequency axis
    freq = np.fft.fftfreq(len(data))

    # Apply the filter
    fft_filtered = np.where(np.abs(freq) <= normalized_cutoff_freq, fft, 0)

    # Perform the inverse Fourier transform
    filtered_signal = np.fft.ifft(fft_filtered)

    # Return the filtered signal
    return np.real(filtered_signal)
