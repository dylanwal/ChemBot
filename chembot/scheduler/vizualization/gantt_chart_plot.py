from typing import Iterator
from datetime import datetime, timedelta

import plotly.graph_objs as go

from scheduler.vizualization.gantt_chart import GanttChart, TimeBlock


class ConfigPlot:
    BAR = "bar"
    BOX = "box"

    def __init__(self):
        self.mode = "box"  # box or bar
        self.showlegend = False
        self.hover = True
        self.max_rows = 6

        # current time
        self.past_time_color = "rgba(200,200,200,0.4)"
        self.now_line_color = "rgba(0,0,0,0.8)"

        # window
        self.background_color = 'rgba(255,255,255,1)'
        self.show_axis = True
        self.margin = dict(l=10, r=10, b=10, t=40, pad=0)
        self.width = 1200
        self.height_per_row = 50
        self.height = None
        self.step = 1  # do not change
        self.x_slider_division = 10

        # bar figure
        self.bar_line_width = 5
        self.bar_vertical_span = 0.3

        # box figure
        self.box_line_width = 30
        self.box_width = self.step/3

    def get_y_values(self, num_rows: int) -> Iterator[int | float]:
        return range(1, num_rows + 1, self.step)

    def get_height(self, num_rows: int) -> int:
        if self.height is not None:
            return self.height

        return self.height_per_row * num_rows + 150

    def layout_kwargs(self, data: GanttChart) -> dict:
        kwargs = {
            "plot_bgcolor": self.background_color,
            "paper_bgcolor": self.background_color,
            "width": self.width,
            "showlegend": False,
            "height": self.get_height(data.number_of_rows),
            "margin": self.margin,
            "xaxis": self.x_axis_layout(data),
            "yaxis": self.y_axis_layout(data),
        }

        return kwargs

    def x_axis_layout(self, data: GanttChart) -> dict:
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
            "range": (data.time_min, data.time_max),
            "rangeselector": self.layout_range_slider(),
            "rangeslider": dict(visible=True, bordercolor="black", borderwidth=3, thickness=0.1)
        }

    def y_axis_layout(self, data: GanttChart) -> dict:
        return {
            "visible": self.show_axis,
            "linecolor": 'black',
            "linewidth": 5,
            "ticks": "outside",
            "tickwidth": 4,
            "showgrid": True,
            "gridcolor": "lightgray",
            "mirror": True,
            "range": (1 - self.step, data.number_of_rows + self.step),
            "tickmode": 'array',
            "tickvals": tuple(self.get_y_values(data.number_of_rows)),
            "ticktext": data.row_labels
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

    def box_kwargs(self, text: str = None) -> dict:
        kwargs = {}
        if self.hover and text is not None:
            # kwargs["text"] = text
            kwargs["hovertext"] = text

        return kwargs

    def current_time_kwargs(self) -> dict:
        return {
            "fillcolor": self.past_time_color,
            "line": {"color": self.now_line_color}
        }


def create_bar(fig: go.Figure, time_block: TimeBlock, y: float, config: ConfigPlot):
    fig.add_trace(
        go.Scatter(
            x=[time_block.time_start, time_block.time_start, time_block.time_start,
               time_block.time_end, time_block.time_end, time_block.time_end],
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
            x=(time_block.time_start, time_block.time_start),
            y=[y - config.bar_vertical_span, y + config.bar_vertical_span],
            mode="lines",
            line={"color": "black", "width": config.bar_line_width},
            **config.scatter_kwargs(time_block.hover_text)
        )
    )


def create_box(fig: go.Figure, time_block: TimeBlock, y: float, config: ConfigPlot):
    fig.add_trace(
        go.Scatter(
            x=(time_block.time_start, time_block.time_end),
            y=(y, y),
            mode="lines",
            line={"color": "black", "width": config.box_line_width},
            **config.scatter_kwargs(time_block.hover_text)
        )
    )


def create_box2(fig: go.Figure, time_block: TimeBlock, y: float, config: ConfigPlot):
    delta = (time_block.time_end - time_block.time_start) * 0.05
    fig.add_shape(type="rect",
                  x0=time_block.time_start + delta,
                  y0=y-config.box_width,
                  x1=time_block.time_end - delta,
                  y1=y+config.box_width,
                  line={"color": "black", "width": 1},
                  fillcolor="black",
                  )
    #


def add_current_time(fig: go.Figure, x_min: datetime, x_max: datetime, num_rows: int, config: ConfigPlot):
    fig.add_trace(
        go.Scatter(
            x=[x_min, x_max, x_max, x_min, x_min],
            y=[0, 0, num_rows, num_rows, 0],
            fill="toself",
            **config.current_time_kwargs()
        )
    )


def create_gantt_chart(data: GanttChart, config: ConfigPlot = None) -> go.Figure:
    """ main function """
    if config is None:
        config = ConfigPlot()

    fig = go.Figure()

    for i, row in enumerate(data):
        i = i + 1  # time_start at y=1 instead y=0
        for time_block in row.time_blocks:
            if time_block.time_end is None:
                create_line(fig, time_block, y=i, config=config)
            else:
                if config.mode == ConfigPlot.BOX:
                    create_box2(fig, time_block, y=i, config=config)
                    create_box(fig, time_block, y=i, config=config)
                else:
                    create_bar(fig, time_block, y=i, config=config)

    if data.current_time is not None:
        add_current_time(fig, data.time_min, data.current_time, data.number_of_rows, config)

    fig.update_layout(**config.layout_kwargs(data))
    return fig
