from typing import Sequence

import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go

from chembot.scheduler.vizualization.gantt_chart import Row, ConfigPlot, create_gantt_chart


def gantt_chart_component(app: dash.Dash, data: Sequence[Row], config: ConfigPlot = None) -> html.Div:
    """
    app.run_server(debug=True)
    """
    if config is None:
        config = ConfigPlot()
        config.num_rows = len(data)

    if config.num_rows < config.max_rows:
        return html.Div()

    # Define the layout of the app
    layout = html.Div([
        html.Div([
            dcc.Slider(
                id='slider',
                min=1,
                max=max(config.get_y_values()),
                step=config.step,
                value=1,
                # marks={y_: labels for y_, label in zip(y, labels)},
                vertical=True
            )
        ], style={'float': 'left', 'height': '400px'}),
        html.Div([
            dcc.Graph(id='scatter-plot', figure=create_gantt_chart(data))
        ], style={'margin-left': '40px'})
    ])

    # Define the callback function to update the scatter plot based on the slider value
    @app.callback(
        Output('scatter-plot', 'figure'),
        [Input('slider', 'value')],
        State('scatter-plot', 'figure')
    )
    def update_scatter_plot(value: int, fig: go.Figure):
        # Set custom labels on the y-axis
        fig['layout']['yaxis']['range'] = config.get_window(position=value)
        return fig

    return layout


def create_app(data: Sequence[Row], config: ConfigPlot = None) -> dash.Dash:
    """
    app.run_server(debug=True)
    """
    app = dash.Dash(__name__)
    app.layout(create_gantt_chart(data, config))

    return app
