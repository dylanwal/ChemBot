import time
from typing import Callable

import numpy as np
import plotly.graph_objs as go

import chembot.utils.algorithms.data_filtering as filters


def get_test_signal():
    # Generate a test signal
    sampling_freq = 1000  # Hz
    duration = 2 * np.pi  # seconds
    t = np.linspace(0, duration, int(duration * sampling_freq), endpoint=False)
    x = np.ones_like(t)
    x[int(len(t)/2):] = 0
    signal = x + np.sin(2 * np.pi * 10 * t) + np.sin(2 * np.pi * 20 * t)
    signal2 = x + np.sin(200 * t)
    return t, np.column_stack((signal, signal2))


def get_test_data_signal():
    pass


def apply_filter(t: np.ndarray, signal: np.ndarray, filter_: Callable, kwargs: dict = {}) -> np.ndarray:
    start = time.perf_counter()

    signal_processed = np.empty_like(signal)
    for i in range(0, len(t)):
        signal_processed[i, :] = signal[i, :]
        signal_processed[i, :] = filter_(t[:i+1], signal_processed[:i+1, :], kwargs)

    end = time.perf_counter()
    print(filter_.__name__, end-start)
    return signal_processed


def filter_interface_exponential(t: np.ndarray, signal: np.ndarray, kwargs: dict = {}):
    if signal.shape[0] < filters.filter_exponential.min_number_points:
        return signal[-1, :]

    return filters.filter_exponential(signal[-2, :], signal[-1, :], **kwargs)


# def filter_interface_fft(t: np.ndarray, signal: np.ndarray, kwargs: dict = {}):
#     if signal.shape[0] < filters.filter_low_pass_fft.min_number_points:
#         return signal[-1, :]
#
#     return filters.filter_low_pass_fft(signal)
from scipy.signal import butter, filtfilt

cutoff_freq = 15
sample_rate = 1000
order = 3
nyquist_freq = 0.5 * sample_rate
normalized_cutoff_freq = cutoff_freq / nyquist_freq
b, a = butter(order, normalized_cutoff_freq)


def filter_interface_butter(t: np.ndarray, signal: np.ndarray, kwargs: dict = {}):
    if signal.shape[0] < 20:
        return signal[-1, :]

    signal_out = np.empty_like(signal)
    for col in range(signal.shape[1]):
        signal_out[-20:, col] = filtfilt(b, a, signal[-20:, col])
    return signal_out[-1, :]


def add_traces(fig, t, signals):
    for i in range(signals.shape[1]):
        fig.add_trace(go.Scatter(x=t, y=signals[:, i], mode="lines"))


def main():
    t, signals = get_test_signal()
    fig = go.Figure()
    fig.add_traces(go.Scatter(x=t, y=np.sin(t), mode="lines", name="original"))
    add_traces(fig, t, signals)

    signals_exponential = apply_filter(t, signals, filter_interface_exponential, {"a": 0.99})
    add_traces(fig, t, signals_exponential)

    signals_butter = apply_filter(t, signals, filter_interface_butter)
    add_traces(fig, t, signals_butter)


    fig.write_html("temp.html", auto_open=True)


if __name__ == "__main__":
    main()
