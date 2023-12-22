import functools

import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots

from unitpy import U, Quantity, Unit


def get_index(x: np.ndarray, value: float) -> int:
    return int(np.argmin(np.abs(x-value)))

def func(t, x_0: float, delta: float, T: float, rad: float):
    return x_0 * (1 + delta * np.sin((2 * np.pi * t) / T + rad))


def calc_derivative(func, t, h):
    # Calculate the numerical derivative using the central difference method
    f_prime = (func(t + h) - func(t - h)) / (2 * h)
    return f_prime


def find_max_derivative(func, t):
    max_derivative = 0
    t_max_derivative = 0

    h = t[1] - t[0]
    for t_ in t:
        derivative = calc_derivative(func, t_, h)
        if derivative > max_derivative:
            max_derivative = derivative
            t_max_derivative = t_

    print("max_temp change", max_derivative, "degC/min", t_max_derivative)


def main():
    t_total = 444
    n = t_total * 6
    t = np.linspace(0, t_total, n)  # minutes
    res_time = func(t, 7, 0.7143, 55.5, np.pi)
    light = func(t, 0.425, 0.8824, 222, np.pi)
    cat_ratio = func(t, 8.75E-5, 0.7143, 111, 0)
    temp = func(t, 303.15, 0.066, 444, 0) - 273

    print("reactor volume: ", t_total / np.mean(res_time), "min")
    print("volume needed:", t_total / np.mean(res_time) * 0.52, "ml")
    find_max_derivative(functools.partial(func, x_0=303.15, delta=0.066, T=444, rad=0), t)

    # fig = go.Figure()
    # fig.add_trace(go.Scatter(x=t, y=res_time))
    # fig.add_trace(go.Scatter(x=t, y=light))
    # fig.add_trace(go.Scatter(x=t, y=cat_ratio))
    # fig.add_trace(go.Scatter(x=t, y=temp))
    # fig.write_html("temp.html", auto_open=True)

    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, subplot_titles=['res_time', 'light', 'cat_ratio', 'temp'])
    fig.add_trace(go.Scatter(x=t, y=res_time), row=1, col=1)
    fig.add_trace(go.Scatter(x=t, y=light), row=2, col=1)
    fig.add_trace(go.Scatter(x=t, y=cat_ratio), row=3, col=1)
    fig.add_trace(go.Scatter(x=t, y=temp), row=4, col=1)
    fig.layout.showlegend = False
    fig.write_html("temp0.html", auto_open=True)


    reactor_length = 115 * U.cm
    reactor_diameter = 0.762 * U.mm
    reactor_volume = (reactor_length * np.pi * (reactor_diameter / 2) ** 2).to("ml")
    C_cat = 0.000733 * U.M
    C_mon = 3.5 * U.M
    print("C_mon:", C_mon, "M | C_cat:", C_cat, "M")

    flow_rate_total = reactor_volume / (res_time * U.min)  # ml/min
    flow_rate_fl = flow_rate_total/2
    flow_rate_mon = ((2 * U.M) * flow_rate_fl / C_mon).to("ml/min")
    flow_rate_cat = (cat_ratio * flow_rate_mon * C_mon / C_cat).to("ml/min")
    flow_rate_dmso = flow_rate_fl - flow_rate_mon - flow_rate_cat

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=flow_rate_dmso.to("ml/min").v, name="flow_rate_dmso"))
    fig.add_trace(go.Scatter(x=t, y=flow_rate_mon.to("ml/min").v, name="flow_rate_mon"))
    fig.add_trace(go.Scatter(x=t, y=flow_rate_cat.to("ml/min").v, name="flow_rate_cat"))
    fig.add_trace(go.Scatter(x=t, y=flow_rate_fl.to("ml/min").v, name="flow_rate_fl"))
    fig.add_trace(go.Scatter(x=t, y=flow_rate_total.to("ml/min").v, name="flow_rate_total"))
    h = np.max(flow_rate_total)

    t_breaks = get_time_breaks(t * Unit.min, flow_rate_mon, 5 * Unit.ml)
    t_breaks_fl = get_time_breaks(t * Unit.min, flow_rate_fl, 6 * Unit.ml)
    for t_break in t_breaks:
        fig.add_trace(go.Scatter(x=[t_break, t_break], y=[0, h.v], legendgroup="breaks", name="break",
                                 line={"color": "black"}))
    for t_break in t_breaks_fl:
        fig.add_trace(go.Scatter(x=[t_break, t_breaks_fl], y=[0, h.v], legendgroup="breaks_fl", name="break_fl",
                                 line={"color": "black"}))

    valleys = find_valleys(flow_rate_mon.v)
    index_ = [valley[2] for valley in valleys]
    np_index = np.array(index_, dtype=np.uint32)
    fig.add_trace(go.Scatter(x=t[np_index], y=flow_rate_mon.v[np_index], mode="markers"))

    fig.write_html("temp1.html", auto_open=True)

    i_index = [get_index(t, t_) for t_ in t_breaks_fl]  # index_
    i_index.insert(0, 0)
    i_index.append(-1)
    print()
    print(i_index)
    print(t[i_index])
    print("index", "mon", "cat", "dmso", "fl")
    for i in range(1, len(i_index)):
        print(i,
              np.trapz(x=t[i_index[i-1]:i_index[i]], y=flow_rate_mon.v[i_index[i-1]:i_index[i]]),
              np.trapz(x=t[i_index[i-1]:i_index[i]], y=flow_rate_cat.v[i_index[i-1]:i_index[i]]),
              np.trapz(x=t[i_index[i - 1]:i_index[i]], y=flow_rate_dmso.v[i_index[i - 1]:i_index[i]]),
              np.trapz(x=t[i_index[i - 1]:i_index[i]], y=flow_rate_fl.v[i_index[i - 1]:i_index[i]])
              )

    data = np.column_stack((t, temp, light, flow_rate_mon.v, flow_rate_cat.v, flow_rate_dmso.v, flow_rate_fl.v))
    np.savetxt("DW2_14_profiles.csv", data, delimiter=",")

    # print("last stretch", np.trapz(x=t[index_[-2]:], y=flow_rate_mon.v[index_[-2]:]))


def get_time_breaks(t: Quantity, flow_rate: Quantity, target: Quantity):
    area = 0
    break_times = []
    flow_rate = flow_rate.to("ml/min").v
    t = t.to("min").v
    target = target.to("ml").v
    for i in range(1, flow_rate.size):
        area += (t[i] - t[i-1]) * (flow_rate[i] + flow_rate[i-1])/2
        if area >= target:
            area = 0
            break_times.append(t[i])

    return break_times


def find_valleys(arr):
    """
    Find the lowest point in each valley within a 1D NumPy array.

    Parameters:
    - arr: NumPy array
        The 1D array containing the function.

    Returns:
    - valley_minima: list of tuples
       (start_index, end_index, lowest_index, lowest_value)
    """
    valley_minima = []
    start_index = 0
    end_index = 0
    descending = False
    lowest_value = None
    lowest_index = None

    for i in range(1, len(arr)):
        if arr[i - 1] < arr[i]:
            # Ascending
            if descending:
                lowest_value = arr[i-1]
                lowest_index = i - 1
                descending = False

        elif arr[i - 1] > arr[i]:
            # Descending
            if not descending:
                # starting the descent
                descending = True
                start_index = i
                if lowest_value is not None:
                    end_index = i-1
                    valley_minima.append((start_index, end_index, lowest_index, lowest_value))
                    lowest_value = None
                    lowest_index = None
    else:
        if lowest_value is not None:
            end_index = len(arr)
            valley_minima.append((start_index, end_index, lowest_index, lowest_value))

    return valley_minima


if __name__ == "__main__":
    main()