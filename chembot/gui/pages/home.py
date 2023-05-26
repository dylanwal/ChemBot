
from dash import Dash, html, dcc, Output, Input, State
import dash_bootstrap_components as dbc

from chembot.gui.app import IDDataStore
from chembot.gui.gui_data import GUIData
from chembot.master_controller.registry import EquipmentRegistry
from chembot.equipment.equipment_interface import EquipmentInterface
from chembot.rabbitmq.messages import JSON_to_class


class IDHome:
    REFRESH_INTERVAL = "refresh_interval"
    REFRESH_DROPDOWN = "refresh_dropdown"
    EQUIPMENT_STATUS = "equipment_status"


def row_layout(equipment: EquipmentInterface):
    return dbc.ListGroupItem(
        [
        html.Div(
            [
                html.H5(equipment.name, className="mb-1"),
                html.Small(equipment.state.name, className="text-success"),
            ],
            className="d-flex w-100 justify-content-between",
        ),
            html.P("fish")
            ] + [html.P(f"{name}: {value}") for name, value in equipment.parameters.items()],
        # html.P("And some text underneath", className="mb-1"),
        # html.Small("Plus some small print.", className="text-muted"),
        color="primary"
    )


def layout_home(app: Dash) -> html.Div:

    @app.callback(
        Output(IDHome.EQUIPMENT_STATUS, "children"),
        [Input(IDDataStore.EQUIPMENT_REGISTRY, "data")]
    )
    def refresh_equipment_status(data: dict[str, object]):
        equipment_registry: EquipmentRegistry = JSON_to_class(data)
        equip_layouts = [row_layout(equip) for equip in equipment_registry.equipment.values()]
        return [dbc.ListGroup(equip_layouts)]

    @app.callback(
        Output(IDHome.REFRESH_INTERVAL, "interval"),
        Input(IDHome.REFRESH_DROPDOWN, "value"),
    )
    def refresh_dropdown(value: str):
        return int(value) * 1000

    return html.Div(children=[
        dcc.Interval(id=IDHome.REFRESH_INTERVAL, interval=GUIData.default_refresh_rate * 1000, n_intervals=-1),
        dbc.Row(
            [
                dbc.Col([html.H1(children='Instrument Status')]),
                dbc.Col(html.P("Refresh Rate (sec):", style={"text-align": "center"}), width=1),
                dbc.Col([
                    dbc.Select(GUIData.refresh_rates, GUIData.default_refresh_rate, id=IDHome.REFRESH_DROPDOWN)
                    ], width=1)
            ]
        ),
        html.Div(id=IDHome.EQUIPMENT_STATUS, children=[]),
    ])
