from typing import Sequence, Iterator, Collection
from datetime import datetime

import plotly.graph_objs as go


class TimeBlock:
    def __init__(self, start: datetime, end: datetime = None, name: str = None, args: str = None):
        self.start = start
        self.end = end
        self.name = name
        self.args = args


class Row:
    def __init__(self, name: str, time_blocks: Collection[TimeBlock]):
        self.name = name
        self.time_blocks = time_blocks


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

        # bar figure
        self.bar_line_width = 5
        self.bar_vertical_span = 0.3

        # box figure
        self.box_line_width = 30

        self.num_rows = 1

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
            "xaxis": {
                "visible": self.show_axis,
                "linecolor": 'black',
                "linewidth": 5,
                "ticks": "outside",
                "tickwidth": 4,
                "showgrid": True,
                "gridcolor": "lightgray",
                "mirror": True,

            },
            "yaxis": {
                "visible": self.show_axis,
                "linecolor": 'black',
                "linewidth": 5,
                "ticks": "outside",
                "tickwidth": 4,
                "showgrid": True,
                "gridcolor": "lightgray",
                "mirror": True,
                "range": (1 - self.step, self.num_rows + self.step)
            }
        }

        return kwargs

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

    @property
    def y_max(self) -> int | float:
        return self.num_rows * self.step

    @property
    def y_min(self) -> int | float:
        return 1

    def get_window(self, position: int | float) -> tuple[int | float, int | float]:
        half_rows = int(self.max_rows/2)
        if position <= self.y_min + self.step * half_rows:
            # bottom limit of window
            return self.y_min - self.step, self.y_min + self.step * self.max_rows
        elif position >= self.y_max - self.step * half_rows:
            # top limit of window
            return self.y_max - self.step * self.max_rows, self.y_min + self.step

        return position - half_rows * self.step, position + half_rows * self.step


def create_bar(fig: go.Figure, time_block: TimeBlock, y: float, config: ConfigPlot):
    fig.add_trace(
        go.Scatter(
            x=[time_block.start, time_block.start, time_block.start,
               time_block.end, time_block.end, time_block.end],
            y=[y-config.bar_vertical_span, y+config.bar_vertical_span, y, y,
               y-config.bar_vertical_span, y+config.bar_vertical_span],
            mode="lines",
            line={"color": "black", "width": config.bar_line_width},
            **config.scatter_kwargs(time_block.args)
        )
    )


def create_line(fig: go.Figure, time_block: TimeBlock, y: float, config: ConfigPlot):
    fig.add_trace(
        go.Scatter(
            x=(time_block.start, time_block.start),
            y=[y-config.bar_vertical_span, y+config.bar_vertical_span],
            mode="lines",
            line={"color": "black", "width": config.bar_line_width},
            **config.scatter_kwargs(time_block.args)
        )
    )


def create_box(fig: go.Figure, time_block: TimeBlock, y: float, config: ConfigPlot):
    fig.add_trace(
        go.Scatter(
            x=(time_block.start, time_block.end),
            y=(y, y),
            mode="lines",
            line={"color": "black", "width": config.box_line_width},
            **config.scatter_kwargs(time_block.args)
        )
    )


def create_gantt_chart(data: Sequence[Row], config: ConfigPlot = None) -> go.Figure:
    if config is None:
        config = ConfigPlot()
        config.num_rows = len(data)

    fig = go.Figure()

    for i, row in zip(config.get_y_values(), data):
        for time_block in row.time_blocks:
            if time_block.end is None:
                create_line(fig, time_block, y=i, config=config)
            else:
                if config.mode == ConfigPlot.BOX:
                    create_box(fig, time_block, y=i, config=config)
                else:
                    create_bar(fig, time_block, y=i, config=config)

    # Set custom labels on the y-axis
    fig.update_layout(**config.layout_kwargs())
    fig.update_layout(
        yaxis=dict(
            tickmode='array',
            tickvals=tuple(config.get_y_values()),
            ticktext=tuple(row.name for row in data)
        ),
    )

    return fig
