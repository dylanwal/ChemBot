import functools

import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots


def func(t, x_0: float, delta: float, T: float, rad: float):
    return x_0*(1+delta*np.sin((2*np.pi*t)/T+rad))


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

    print(max_derivative, t_max_derivative)


def main():
    n = 1_000
    t_total = 444
    t = np.linspace(0, t_total, n)  # minutes
    res_time = func(t, 7, 0.7143, 55.5, np.pi)
    light = func(t, 0.425, 0.8824, 222, np.pi)
    cat_ratio = func(t, 8.75E-3, 0.7143, 111, 0)
    temp = func(t, 303.15, 0.066, 444, 0) - 273

    print("reactor volume: ", t_total/np.mean(res_time), "min")
    print("volume needed:", t_total/np.mean(res_time)*0.52, "ml")
    find_max_derivative(functools.partial(func, x_0=303.15, delta=0.066, T=444, rad=0), t)

    # fig = go.Figure()
    # fig.add_trace(go.Scatter(x=t, y=res_time))
    # fig.add_trace(go.Scatter(x=t, y=light))
    # fig.add_trace(go.Scatter(x=t, y=cat_ratio))
    # fig.add_trace(go.Scatter(x=t, y=temp))
    # fig.write_html("temp.html", auto_open=True)

    # fig = make_subplots(rows=4, cols=1, shared_xaxes=True, subplot_titles=['res_time', 'light', 'cat_ratio', 'temp'])
    # fig.add_trace(go.Scatter(x=t, y=res_time), row=1, col=1)
    # fig.add_trace(go.Scatter(x=t, y=light), row=2, col=1)
    # fig.add_trace(go.Scatter(x=t, y=cat_ratio), row=3, col=1)
    # fig.add_trace(go.Scatter(x=t, y=temp), row=4, col=1)
    # fig.write_html("temp.html", auto_open=True)

if __name__ == "__main__":
    main()
