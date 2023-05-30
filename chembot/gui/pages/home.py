from dash import Dash, html, dcc, Output, Input, State, MATCH
import dash_bootstrap_components as dbc

from chembot.gui.app import IDDataStore
from chembot.gui.gui_data import GUIData
from chembot.master_controller.registry import EquipmentRegistry
from chembot.equipment.equipment_interface import EquipmentInterface, EquipmentState, Action, ActionParameter
from chembot.rabbitmq.messages import JSON_to_class


class IDHome:
    REFRESH_INTERVAL = "refresh_interval"
    REFRESH_DROPDOWN = "refresh_dropdown"
    EQUIPMENT_STATUS = "equipment_status"


STATUS_COLORS = {
    EquipmentState.OFFLINE: "text-dark",
    EquipmentState.PREACTIVATION: "text-dark",
    EquipmentState.STANDBY: "text-success",
    EquipmentState.SCHEDULED_FOR_USE: "text-warning",
    EquipmentState.RUNNING: "text-info",
    EquipmentState.RUNNING_BUSY: "text-info",
    EquipmentState.SHUTTING_DOWN: "text-info",
    EquipmentState.CLEANING: "text-info",
    EquipmentState.ERROR: "text-danger",
}


def equipment_layout(equipment: EquipmentInterface):
    return dbc.ListGroupItem(
        [
            html.Div(
                [
                    html.Div([
                        html.H5(equipment.name, className="mb-1", style={"text-decoration": "underline"}),
                        html.P(f"({equipment.class_})"),
                    ], className="d-inline-flex w-100 justify-content-start"),
                    html.Small(equipment.state.name, className=STATUS_COLORS[equipment.state]),
                ],
                className="d-flex w-100 justify-content-between",
            ),
            html.Div(id={"type": "equipment_details", "index": equipment.name})
        ],
        color="primary",
        n_clicks=0,
        action=True,
        id={"type": "equipment_item", "index": equipment.name}
    )


def get_action_list(action: Action):
    return dbc.ListGroupItem(
        [
            html.Div([
                html.P(action.name, className="mb-1", style={"text-decoration": "underline"}),
                html.P("  :  " + "".join(action.description)),
            ],
                     className="d-inline-flex w-100 justify-content-start"
            ),
            html.P("Input:"),
            html.Div(get_parameters_layout(action.inputs)),
            html.P("Output:"),
            html.Div(get_parameters_layout(action.outputs)),
        ],
        color="secondary",
    )


def get_parameters_layout(parameters: list[ActionParameter]):
    if not parameters:
        return "---> None"

    return [get_parameter_layout(parameter) for parameter in parameters]


def get_parameter_layout(parameter: ActionParameter):
    return html.Div([
                html.P("---> "),
                html.P(parameter.name, className="mb-1", style={"text-decoration": "underline"}),
                html.P(f"({parameter.types}): {parameter.descriptions}"),
            ],
                     className="d-inline-flex w-100 justify-content-start"
            )


def layout_home(app: Dash) -> html.Div:
    @app.callback(
        Output({"type": "equipment_details", "index": MATCH}, "children"),
        Input({"type": "equipment_item", "index": MATCH}, "n_clicks"),
        [Input({"type": "equipment_item", "index": MATCH}, "id"), State(IDDataStore.EQUIPMENT_REGISTRY, "data")]
    )
    def equipment_dropdown(n_clicks: int, id_: dict, data: dict[str, object]):
        if n_clicks % 2 == 0:
            return []

        equipment = id_["index"]
        equipment_registry: EquipmentRegistry = JSON_to_class(data)
        equipment_interface: EquipmentInterface = equipment_registry.equipment[equipment]

        actions = []
        for action in equipment_interface.actions:
            actions.append(get_action_list(action))

        return [
            html.P(" ||  ".join(f"{name}: {value}" for name, value in equipment_interface.parameters.items())),
            dbc.ListGroup(actions)
            ]

    @app.callback(
        Output(IDHome.EQUIPMENT_STATUS, "children"),
        [Input(IDDataStore.EQUIPMENT_REGISTRY, "data")]
    )
    def refresh_equipment_status(data: dict[str, object]):
        equipment_registry: EquipmentRegistry = JSON_to_class(data)
        equip_layouts = [equipment_layout(equip) for equip in equipment_registry.equipment.values()]
        return [dbc.ListGroup(equip_layouts)]

    @app.callback(
        Output(IDHome.REFRESH_INTERVAL, "interval"),
        Input(IDHome.REFRESH_DROPDOWN, "value"),
    )
    def refresh_dropdown(value: str):
        return int(value) * 1000

    @app.callback(
        Output(IDHome.REFRESH_INTERVAL, "interval"),
        Input('interval-component', 'n_intervals'),
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
