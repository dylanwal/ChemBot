import numpy as np

import plotly.graph_objs as go
from plotly.subplots import make_subplots
from unitpy import Unit, Quantity

from chembot.utils.algorithms.change_detection import CUSUM


class Slug:
    sensor_spacer = 0.95 * Unit.cm
    tube_diameter = 0.0762 * Unit.cm
    __slots__ = ("time_start_1", "time_end_1", "time_start_2", "time_end_2", "_length", "_velocity")

    def __init__(self,
                 time_start_1: float | int,
                 time_end_1: float | int = None,
                 time_start_2: float | int = None,
                 time_end_2: float | int = None,
                 velocity: Quantity | None = None
                 ):
        self.time_start_1 = time_start_1
        self.time_end_1 = time_end_1
        self.time_start_2 = time_start_2
        self.time_end_2 = time_end_2
        self._length = None
        self._velocity = velocity

    def __str__(self):
        if self.volume is not None:
            text = f"vel:{self.velocity:3.2f}, len: {self.length:3.2f}, vol:{self.volume:3.2f}"
        elif self.time_span:
            text = f"start: {self.time_start_1:3.2f}"
            if self.velocity is not None:
                text += f", velocity: {self.velocity:3.2f})"
        else:
            text = f"start: {self.time_start_1:3.2f}, No end detected"

        return text

    @property
    def time_span(self) -> Quantity | None:
        if self.time_end_1 is None:
            return None
        t = self.time_end_1 - self.time_start_1
        if isinstance(t, Quantity):
            return t
        return t * Unit.s

    @property
    def time_offset(self):
        if self.is_complete:
            t = (self.time_start_2 - self.time_start_1 + self.time_end_2 - self.time_end_1) / 2
            if isinstance(t, Quantity):
                return t
            return t * Unit.s
        return None

    @property
    def is_complete(self) -> bool:
        return not (self.time_end_1 is None or self.time_end_2 is None or self.time_start_2 is None)

    @property
    def velocity(self) -> Quantity | None:
        if self._velocity is None:
            if not self.is_complete:
                return None
            self._velocity = self.sensor_spacer / self.time_span

        return self._velocity.to("mm/s")

    @property
    def length(self) -> Quantity | None:
        if self._length is None:
            if self.velocity is None or self.time_span is None:
                return None
            self._length = self.velocity * self.time_span

        return self._length.to('mm')

    @property
    def volume(self) -> Quantity | None:
        if self.length is None:
            return None
        return (self.length * np.pi * (self.tube_diameter / 2) ** 2).to("uL")


def main2(path):
    velocity = 0.3 * Unit("ml/min") / (np.pi * (Slug.tube_diameter / 2) ** 2)
    data = np.genfromtxt(path, delimiter=",")
    data[:, 0] = data[:, 0] - data[0, 0]

    algorithm = CUSUM()
    slugs = []
    up = np.zeros(data.shape[0])
    down = np.zeros(data.shape[0])
    for i in range(data.shape[0]):
        new_data_point = data[i, 1]
        event = algorithm.add_data(new_data_point)
        up[i] = algorithm._up_sum
        down[i] = algorithm._low_sum
        if event is CUSUM.States.up:
            slugs.append(Slug(time_start_1=data[i, 0], velocity=velocity))
        if event is CUSUM.States.down and slugs:
            slugs[-1].time_end_1 = data[i, 0]

    # printing
    for i, slug in enumerate(slugs):
        print(i, slug)
    print("avg. volume: ", sum([slug.volume for slug in slugs[:-1]]) / len(slugs))

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=data[:, 0], y=data[:, 1], mode="lines"))
    fig.add_trace(go.Scatter(x=data[:, 0], y=data[:, 2], mode="lines"))
    fig.add_trace(
        go.Scatter(x=data[:, 0], y=up, mode="lines", legendgroup="CUSUM"),
        secondary_y=False
    )
    fig.add_trace(
        go.Scatter(x=data[:, 0], y=down, mode="lines", legendgroup="CUSUM"),
        secondary_y=False
    )
    for slug in slugs:
        add_slug(fig, slug)

    fig.write_html("temp.html", auto_open=True)


def add_slug(fig, slug: Slug):
    x = [slug.time_start_1, slug.time_start_1, slug.time_start_1, slug.time_end_1, slug.time_end_1, slug.time_end_1]
    y = [-1, 1, 0, 0, 1, -1]
    fig.add_trace(
        go.Scatter(x=x, y=y, mode="lines", legendgroup="process"),
        secondary_y=True
    )


def main(path):
    data = np.genfromtxt(path, delimiter=",")
    data[:, 0] = data[:, 0] - data[0, 0]

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
    # fig.add_trace(
    #     go.Scatter(x=data[:, 0], y=state, mode="lines", legendgroup="process"),
    #               secondary_y=True
    # )

    fig.write_html("temp.html", auto_open=True)


if __name__ == "__main__":
    path_ = r"C:\Users\nicep\Desktop\Reseach_Post\python\chembot\chembot\equipment\sensors\phase_sensor\develop" \
            r"\data_0.csv"
    main2(path_)
