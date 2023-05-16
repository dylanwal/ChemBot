
from dash import Dash, html, dcc, Output, Input
import dash_bootstrap_components as dbc


class IDHome:
    REFRESH_INTERVAL = "refresh_interval"
    REFRESH_DROPDOWN = "refresh_dropdown"
    EQUIPMENT_STATUS = "equipment_status"


def layout_home(app: Dash) -> html.Div:
    @app.callback(Output(IDHome.EQUIPMENT_STATUS, "children"), [Input(IDHome.REFRESH_INTERVAL, "n_intervals")])
    def refresh_equipment_status(_: int) -> html.Div:
        equips = [equip.data_row() for equip in gui.equipment_registry.equipment.values()]

        headers = html.Thead(html.Tr([html.Th(k) for k in equips[0]]), className='table-primary')
        rows = [html.Tr([html.Td(v) for v in equip.values()], className='table-secondary') for equip in equips]

        return html.Div([
            dbc.Label('Equipment Status'),
            dbc.Row([
                dbc.Col(dbc.Table([headers, html.Tbody(rows)], bordered=True, hover=True, size='sm')),
                dbc.Col()
                ])
        ])

    @app.callback(
        Output(IDHome.REFRESH_INTERVAL, "interval"),
        Input(IDHome.REFRESH_DROPDOWN, "value"),
    )
    def refresh_dropdown(value: str):
        return int(value) * 1000

    return html.Div(children=[
        dcc.Interval(id=IDHome.REFRESH_INTERVAL, interval=gui.data.default_refresh_rate * 1000, n_intervals=-1),
        dbc.Row(
            [
                dbc.Col([html.H1(children='Instrument Status')]),
                dbc.Col(html.P("Refresh Rate (sec):", style={"text-align": "center"}), width=1),
                dbc.Col([
                    dbc.Select(gui.data.refresh_rates, gui.data.default_refresh_rate, id=IDHome.REFRESH_DROPDOWN)
                    ], width=1)
            ]
        ),
        html.Div(id=IDHome.EQUIPMENT_STATUS),
    ])
