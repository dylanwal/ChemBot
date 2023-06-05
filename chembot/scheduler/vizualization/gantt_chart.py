from typing import Sequence, Iterator
from datetime import datetime, timedelta

import plotly.graph_objs as go


class TimeBlock:
    counter = 0

    def __init__(self, start: datetime, end: datetime = None, name: str = None, hover_text: str = None):
        self.start = start
        self.end = end
        self.name = name if name is None else f"time_block_{self.counter}"
        self.hover_text = hover_text

        TimeBlock.counter += 1


class Row:
    def __init__(self, name: str, time_blocks: Sequence[TimeBlock]):
        self.name = name
        self.time_blocks = time_blocks

    def __len__(self) -> int:
        return len(self.time_blocks)

    @property
    def time_block_names(self):  # -> Generator[str]:
        return (time_block.name for time_block in self.time_blocks)


def get_min_max_time(data: Sequence[Row]) -> tuple[datetime, datetime]:
    min_time = data[0].time_blocks[0].start
    max_time = min_time
    for row in data:
        for time_block in row.time_blocks:
            if time_block.start < min_time:
                min_time = time_block.start
                continue
            if time_block.end is not None and time_block.end > max_time:
                max_time = time_block.end

    return min_time, max_time


def get_time_delta_label(time_delta: timedelta) -> str:
    if time_delta >= timedelta(days=1):
        return f"{time_delta.days} d"
    if time_delta >= timedelta(hours=1):
        return f"{int(time_delta.seconds / 60 / 60)} h"
    if time_delta >= timedelta(minutes=1):
        return f"{int(time_delta.seconds / 60)} min"
    if time_delta >= timedelta(seconds=1):
        return f"{time_delta.seconds} s"
    return f"{time_delta.microseconds} ms"


def linspace_datetime(start: datetime, end: datetime, n: int) -> list[datetime]:
    time_span = (end - start).total_seconds()
    interval = time_span / n
    return [start + i * timedelta(seconds=interval) for i in range(n)]


class ConfigPlot:
    BAR = "bar"
    BOX = "box"

    def __init__(self):
        self.mode = "box"  # box or bar
        self.showlegend = False
        self.hover = True
        self.max_rows = 6

        # window
        self.background_color = 'rgba(255,255,255,1)'
        self.show_axis = True
        self.margin = dict(l=10, r=10, b=10, t=50, pad=0)
        self.width = 1200
        self.height_per_row = 50
        self.height = None
        self.step = 1
        self.x_slider_division = 10

        # bar figure
        self.bar_line_width = 5
        self.bar_vertical_span = 0.3

        # box figure
        self.box_line_width = 30

        # attributes set by data
        self.num_rows = 1
        self.min_time = datetime.now()
        self.max_time = datetime.now()
        self.y_axis_labels = []

    @property
    def y_max(self) -> int | float:
        return self.num_rows * self.step

    @property
    def y_min(self) -> int | float:
        return 1

    @property
    def time_range(self) -> timedelta:
        return self.max_time - self.min_time

    def set_data_attributes(self, data: Sequence[Row]):
        self.num_rows = len(data)
        self.min_time, self.max_time = get_min_max_time(data)
        self.y_axis_labels = (row.name for row in data)

    def _get_x_range(self, time_delta: timedelta) -> tuple[datetime, datetime]:
        return self.min_time, self.min_time + time_delta

    def get_height(self) -> int:
        if self.height is not None:
            return self.height

        return self.height_per_row * self.num_rows + 100

    def layout_kwargs(self) -> dict:
        kwargs = {
            "plot_bgcolor": self.background_color,
            "paper_bgcolor": self.background_color,
            "width": self.width,
            "height": self.get_height(),
            "margin": self.margin,
            "xaxis": self.x_axis_layout(),
            "yaxis": self.y_axis_layout(),
        }

        return kwargs

    def x_axis_layout(self) -> dict:
        return {
            "visible": self.show_axis,
            "linecolor": 'black',
            "linewidth": 5,
            "ticks": "outside",
            "tickwidth": 4,
            "showgrid": True,
            "gridcolor": "lightgray",
            "mirror": True,
            "type": "date",
            "rangeselector": self.layout_range_slider(),
            "rangeslider": dict(visible=True, bordercolor="black", borderwidth=3, thickness=0.1)
        }

    def y_axis_layout(self) -> dict:
        return {
            "visible": self.show_axis,
            "linecolor": 'black',
            "linewidth": 5,
            "ticks": "outside",
            "tickwidth": 4,
            "showgrid": True,
            "gridcolor": "lightgray",
            "mirror": True,
            "range": (1 - self.step, self.num_rows + self.step),
            "tickmode": 'array',
            "tickvals": tuple(self.get_y_values()),
            "ticktext": tuple(self.y_axis_labels)
        }

    @staticmethod
    def layout_range_slider():
        return dict(
            buttons=list([
                dict(count=1,
                     label="1sec",
                     step="second",
                     stepmode="backward"),
                dict(count=1,
                     label="1min",
                     step="minute",
                     stepmode="backward"),
                dict(count=1,
                     label="1h",
                     step="hour",
                     stepmode="backward"),
                dict(count=1,
                     label="1d",
                     step="day",
                     stepmode="backward"),
                dict(count=1,
                     label="1m",
                     step="month",
                     stepmode="backward"),
                dict(count=1,
                     label="1y",
                     step="year",
                     stepmode="backward"),
                dict(step="all")
            ]),
            activecolor="#b0b0b0"
        )

    def scatter_kwargs(self, text: str = None) -> dict:
        kwargs = {}

        if not self.showlegend:
            kwargs["showlegend"] = False

        if self.hover and text is not None:
            # kwargs["text"] = text
            kwargs["hovertext"] = text

        return kwargs

    def get_y_values(self) -> Iterator[int | float]:
        return range(1, self.num_rows + 1, self.step)

    def get_window(self, position: int | float) -> tuple[int | float, int | float]:
        half_rows = int(self.max_rows / 2)
        if position <= self.y_min + self.step * half_rows:
            # bottom limit of window
            return self.y_min - self.step, self.y_min + self.step * self.max_rows
        elif position > self.y_max - self.step * half_rows:
            # top limit of window
            return self.y_max - self.step * self.max_rows, self.y_max + self.step
        print("e")
        return position - half_rows * self.step-1, position + half_rows * self.step


def create_bar(fig: go.Figure, time_block: TimeBlock, y: float, config: ConfigPlot):
    fig.add_trace(
        go.Scatter(
            x=[time_block.start, time_block.start, time_block.start,
               time_block.end, time_block.end, time_block.end],
            y=[y - config.bar_vertical_span, y + config.bar_vertical_span, y, y,
               y - config.bar_vertical_span, y + config.bar_vertical_span],
            mode="lines",
            line={"color": "black", "width": config.bar_line_width},
            **config.scatter_kwargs(time_block.hover_text)
        )
    )


def create_line(fig: go.Figure, time_block: TimeBlock, y: float, config: ConfigPlot):
    fig.add_trace(
        go.Scatter(
            x=(time_block.start, time_block.start),
            y=[y - config.bar_vertical_span, y + config.bar_vertical_span],
            mode="lines",
            line={"color": "black", "width": config.bar_line_width},
            **config.scatter_kwargs(time_block.hover_text)
        )
    )


def create_box(fig: go.Figure, time_block: TimeBlock, y: float, config: ConfigPlot):
    fig.add_trace(
        go.Scatter(
            x=(time_block.start, time_block.end),
            y=(y, y),
            mode="lines",
            line={"color": "black", "width": config.box_line_width},
            **config.scatter_kwargs(time_block.hover_text)
        )
    )


def create_gantt_chart(data: Sequence[Row], config: ConfigPlot = None) -> go.Figure:
    """ main function """
    if config is None:
        config = ConfigPlot()
        config.set_data_attributes(data)

    fig = go.Figure()

    # add data
    for i, row in zip(config.get_y_values(), data):
        for time_block in row.time_blocks:
            if time_block.end is None:
                create_line(fig, time_block, y=i, config=config)
            else:
                if config.mode == ConfigPlot.BOX:
                    create_box(fig, time_block, y=i, config=config)
                else:
                    create_bar(fig, time_block, y=i, config=config)

    # Set custom layout
    fig.update_layout(**config.layout_kwargs())

    return fig
