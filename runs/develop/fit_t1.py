import numpy as np
import plotly.graph_objs as go
from scipy.optimize import curve_fit


def equation(t: np.ndarray, a: float, T1: float):
    return a * (1 - 2*np.exp(-t / T1))


def main():
    MA = np.array([
        [0.001, -11.12],
        [2.14379, - 0.137133],
        [4.28657, 5.94406],
        [6.42936, 9.3178],
        [8.57214, 10.9316],
        [10.7149, 12.5955],
        [12.8577, 14.9099],
        [15.0005, 16.2908],
        [17.1433, 17.8073],
        # [19.2861, 17.4581],
        # [21.4289, 16.3596],
        # [23.5716, 15.9451],
        # [25.7144, 14.8885],
        # [27.8572, 11.9438],
        # [30, 9.03118],
    ])

    popt, pcov = curve_fit(equation, xdata=MA[:,0], ydata=MA[:,1])
    print(popt)

    fig =go.Figure()
    fig.add_trace(go.Scatter(x=MA[:,0], y=MA[:,1]))
    fig.add_trace(go.Scatter(x=MA[:,0], y=equation(MA[:,0], *popt), name="fit"))
    fig.write_html("temp.html", auto_open=True)


if __name__ == "__main__":
    main()
