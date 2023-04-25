import dash
from dash import html, dcc

dash.register_page(__name__)

layout = html.Div(children=[
    html.H1(children='Running Jobs'),

    html.H1(children='Add new job'),
]
)