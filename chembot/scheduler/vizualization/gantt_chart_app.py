from typing import Sequence
from datetime import datetime

import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go

from chembot.scheduler.vizualization.gantt_chart import Row, ConfigPlot, create_gantt_chart


def gantt_chart_component(
        app: dash.Dash, data: Sequence[Row],
        current_time: datetime = None,
        config: ConfigPlot = None
) -> html.Div:
    """
    app.run_server(debug=True)
    """
    if config is None:
        config = ConfigPlot()
        config.set_data_attributes(data)

    if config.num_rows < config.max_rows:
        return html.Div()

    # Define the layout of the app
    layout = html.Div([
        html.Div(create_slider(app, data, config), style={'float': 'left', 'height': '450px', 'margin-top': '10px'}),
        html.Div([
            dcc.Graph(id='scatter-plot', figure=create_gantt_chart(data, current_time, config))
        ], style={'margin-left': '60px'})
    ])

    return layout


def create_slider(app: dash.Dash, data: Sequence[Row], config: ConfigPlot):
    if len(data) <= config.max_rows:
        return []

    slider = dcc.Slider(
                id='slider',
                className="slider",
                min=1,
                max=max(config.get_y_values()),
                step=config.step,
                value=1,
                marks={y_: row.name for y_, row in zip(range(1, len(data)), data)},
                vertical=True
            )

    @app.callback(
        Output('scatter-plot', 'figure'),
        [Input('slider', 'value')],
        State('scatter-plot', 'figure')
    )
    def update_scatter_plot(value: int, fig: go.Figure):
        # Set custom labels on the y-axis
        fig['layout']['yaxis']['range'] = config.get_window(position=value)
        return fig

    return slider


def create_app(data: Sequence[Row], current_time: datetime = None, config: ConfigPlot = None) -> dash.Dash:
    """
    app.run_server(debug=True)
    """
    app = dash.Dash(__name__)
    app.layout = gantt_chart_component(app, data, current_time, config)

    return app
