import logging

import plotly.graph_objs as go
from dash import Dash, html, dcc, Output, Input, State, MATCH
import dash_bootstrap_components as dbc

from chembot.configuration import config

logger = logging.getLogger(config.root_logger_name + ".gui")


class IDJobs:
    JOB_QUEUE = "job_queue"
    REFRESH_TIMELINE = "refresh_timeline"
    TIMELINE = "timeline"


# def create_timeline() -> go.Figure:
#     df = pd.DataFrame([
#         dict(Equipment="Serial", Start='2023-01-01', Finish='2023-02-28', Job="expt_1"),
#         dict(Equipment="Red_LED", Start='2023-03-05', Finish='2023-04-15', Job="expt_1"),
#         dict(Equipment="Mint_LED", Start='2023-02-20', Finish='2023-05-30', Job="expt_2")
#     ])
#
#     fig = px.timeline(df, x_start="Start", x_end="Finish", y="Equipment", color="Job")
#     fig.update_yaxes(autorange="reversed")  # otherwise tasks are listed from the bottom up
#     return fig


def layout_jobs(app: Dash) -> html.Div:

    @app.callback(
        Output(IDJobs.TIMELINE, "children"),
        Input(IDJobs.REFRESH_TIMELINE, "n_clicks")
    )
    def layout_timeline(_):
        return [dcc.Graph()] # figure=create_timeline()

    return html.Div(children=[
        dbc.Row(
            [
                dbc.Col([html.H1(children='Instrument Status')]),
                dbc.Col(width=1),
                dbc.Col([
                    dbc.Button("refresh timeline", id=IDJobs.REFRESH_TIMELINE, color="primary", className="me-1")
                ], width=1)
            ]
        ),
        html.Div(id=IDJobs.JOB_QUEUE, children=[]),
        html.H1(children='Timeline'),
        html.Div(id=IDJobs.TIMELINE, children=[])
        ]
    )
