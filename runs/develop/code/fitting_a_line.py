import numpy as np
import plotly.graph_objs as go
import piecewise_regression


def func(x):
    return np.sin(x)

n = 1000

x = np.linspace(0, np.pi * 2, n)
y_exact = func(x)

pw_fit = piecewise_regression.Fit(x, y_exact, n_breakpoints=4)
pw_fit.summary()

xx, yy = pw_fit.plot_fit()

# Plot the equation and line segments
fig = go.Figure()
fig.add_trace(go.Scatter(x=x, y=y_exact, name="exact"))
fig.add_trace(go.Scatter(x=xx, y=yy, name="segments"))
fig.write_html("temp.html", auto_open=True)
