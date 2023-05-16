
import dash
from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc


dash.register_page(__name__, path='/')

default_refresh_rate = 2

layout = html.Div(children=[
    dcc.Interval(id="refresh", interval=default_refresh_rate * 1000, n_intervals=-1),
    dbc.Row(
        [
            dbc.Col([html.H1(children='Instrument Status')]),
            dbc.Col(html.P("Refresh Rate (sec):", style={"text-align": "center"}), width=1),
            dbc.Col([
                dbc.Select([1, 2, 5, 10, 30], default_refresh_rate, id="refresh-dropdown")
                ], width=1)
        ]
    ),
    html.H2(children="text", id="update_p"),
])


@dash.callback(Output("update_p", "children"), [Input("refresh", "n_intervals")])
def update(n_intervals):
    # Do update
    return str(n_intervals)


@dash.callback(
    Output("refresh", "interval"),
    Input("refresh-dropdown", "value"),
)
def refresh_dropdown(value: str):
    return int(value) * 1000
