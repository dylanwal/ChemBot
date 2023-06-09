
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go

from scheduler.vizualization.gantt_chart import GanttChart
from chembot.scheduler.vizualization.gantt_chart_plot import ConfigPlot, create_gantt_chart


def gantt_chart_component(
        app: dash.Dash,
        data: GanttChart,
        config: ConfigPlot = None
) -> html.Div:
    """
    app.run_server(debug=True)
    """
    if config is None:
        config = ConfigPlot()

    if data.number_of_rows < config.max_rows:
        return html.Div()

    # Define the layout of the app
    layout = html.Div([
        html.Div(create_slider(app, data, config), style={'float': 'left', 'height': '450px', 'margin-top': '10px'}),
        html.Div([
            dcc.Graph(id='scatter-plot', figure=create_gantt_chart(data, config))
        ], style={'margin-left': '60px'})
    ])

    return layout


def create_slider(app: dash.Dash, data: GanttChart, config: ConfigPlot):
    if data.number_of_rows <= config.max_rows:
        return []

    slider = dcc.Slider(
                id='slider',
                className="slider",
                min=1,
                max=max(config.get_y_values(data.number_of_rows)),
                step=config.step,
                value=1,
                marks={y_: row.name for y_, row in zip(range(1, data.number_of_rows), data)},
                vertical=True
            )

    @app.callback(
        Output('scatter-plot', 'figure'),
        [Input('slider', 'value')],
        State('scatter-plot', 'figure')
    )
    def update_scatter_plot(position: int, fig: go.Figure):
        # Set custom labels on the y-axis
        fig['layout']['yaxis']['range'] = get_window(position, data.number_of_rows, config.max_rows)
        return fig

    return slider


def get_window(position: int, num_rows: int, max_rows: int) -> tuple[int, int]:
    half_rows = int(max_rows / 2)
    if position <= 1 + half_rows:
        # bottom limit of window
        return 0, max_rows + 1
    elif position > num_rows - half_rows:
        # top limit of window
        return num_rows - max_rows, num_rows + 1
    return position - half_rows-1, position + half_rows


def create_app(data: GanttChart, config: ConfigPlot = None) -> dash.Dash:
    """
    app.run_server(debug=True)
    """
    app = dash.Dash(__name__)
    app.layout = gantt_chart_component(app, data, config)

    return app
