import datetime
import logging

import jsonpickle
from dash import Dash, html, dcc, Input, Output, State, ALL, Patch
import dash_bootstrap_components as dbc

from chembot.configuration import config
from chembot.gui.gui_data import IDData
from chembot.rabbitmq.messages import RabbitMessageAction
from chembot.rabbitmq.rabbit_http_messages import write_and_read_message, read_message
from chembot.equipment.equipment_interface import EquipmentRegistry, ActionParameter, EquipmentInterface, \
    NumericalRangeContinuous, NumericalRangeDiscretized, CategoricalRange
from chembot.master_controller.master_controller import MasterController

logger = logging.getLogger(config.root_logger_name + ".gui")


class IDRabbit:
    SEND_BUTTON = "send_button"
    MESSAGE_DESTINATION = "message_destination"
    SELECT_EQUIPMENT = "select_destination"
    MESSAGE_ACTION = "message_action"
    ACTION_DESCRIPTION = "action_description"
    SELECT_ACTION = "select_action"
    MESSAGE_PARAMETERS = "message_parameters"
    PARAMETERS_GROUP = "parameters_group"
    REPLY_STATUS = "reply_status"
    REPLY = "reply"


def get_parameter_div(param: ActionParameter, index: int) -> dbc.InputGroup:
    children = [dbc.InputGroupText(param.name, id={"type": "parameter_labels", "index": index})]
    # print(param)
    # if param.types == "str":
    #     if isinstance(param.default, NotDefinedParameter):
    #         text = "text"
    #     else:
    #         text = param.default
    #     children.append(dbc.Input(text, id={"type": "parameter", "index": index}))
    #
    # if param.types == "str" and param.range_:  # with options
    #     if isinstance(param.default, NotDefinedParameter):
    #         value = None
    #     else:
    #         value = param.default
    #     range_: CategoricalRange = param.range_
    #     children.append(dbc.Select(id={"type": "parameter", "index": index},
    #                                options=[{"label": v, "value": v} for v in range_.options]))
    #
    # if param.types == "int" or param.types == "float":
    #     children.append(dbc.Input(placeholder="value", type="number", id={"type": "parameter", "index": index}))
    #     if param.unit is not None:
    #         children.append(dbc.InputGroupText(param.unit))
    #     if param.range_ is not None:
    #         children.append(dbc.InputGroupText('range :' + str(param.range_)))
    #
    # if param.types == "bool":
    #     children.append(dbc.Select(options=[{"label": "True", "value": True}, {"label": "False", "value": False}],
    #                                id={"type": "parameter", "index": index}))

    return dbc.InputGroup(children)


def get_equipment_name(text: str) -> str:
    return text.split(" ")[0]


def get_equipment(text: str, data: dict[str, object]) -> EquipmentInterface:
    equipment_name = get_equipment_name(text)
    equipment_registry: EquipmentRegistry = jsonpickle.loads(data)
    return equipment_registry.equipment[equipment_name]


def layout_rabbit(app: Dash) -> html.Div:
    @app.callback(
        Output(IDRabbit.SELECT_EQUIPMENT, "options"),
        [Input(IDData.EQUIPMENT_REGISTRY, "data")],
    )
    def update_equipment_dropdown(data: dict[str, object]) -> list[str]:
        equipment_registry: EquipmentRegistry = jsonpickle.loads(data)
        equipment = [f"{equip.name} ({equip.class_})" for equip in equipment_registry.equipment.values()]
        return equipment

    @app.callback(
        Output(IDRabbit.SELECT_ACTION, "options"),
        Input(IDRabbit.SELECT_EQUIPMENT, "value"),
        State(IDData.EQUIPMENT_REGISTRY, "data")
    )
    def update_action_dropdown(equipment: str | None, data: dict[str, object]) -> list[str]:
        if equipment:
            equipment = get_equipment(equipment, data)
            return [action.name for action in equipment.actions]
        return []

    @app.callback(
        [Output(IDRabbit.PARAMETERS_GROUP, "children"), Output(IDRabbit.ACTION_DESCRIPTION, "children")],
        Input(IDRabbit.SELECT_ACTION, "value"),
        [State(IDData.EQUIPMENT_REGISTRY, "data"), State(IDRabbit.SELECT_EQUIPMENT, "value")]
    )
    def update_parameters_group(action: str, data: dict[str, object], equipment: str | None) -> tuple:
        if equipment is None:
            return [], ""

        parameter_components = []
        equipment = get_equipment(equipment, data)
        action = equipment.get_action(action)
        if action.inputs:
            for i, param in enumerate(action.inputs):
                parameter_components.append(get_parameter_div(param, i))

        description = [html.H5("Description:"), html.P(action.description)]
        return parameter_components, description

    equipment_dropdown = dbc.InputGroup(
        [
            dbc.InputGroupText("equipment"),
            dbc.Select(id=IDRabbit.SELECT_EQUIPMENT, options=[])
        ]
    )
    action_dropdown = dbc.InputGroup(
        [
            dbc.InputGroupText("action"),
            dbc.Select(id=IDRabbit.SELECT_ACTION, options=[])
        ]
    )

    parameter_group = [
        html.H6("Parameters:"),
        html.Div(id=IDRabbit.PARAMETERS_GROUP, children=[])
    ]

    input_group = html.Div([
        html.H3("Send:"),
        dbc.Row(dbc.Col(id=IDRabbit.MESSAGE_DESTINATION, children=[equipment_dropdown], width=4)),
        dbc.Row(dbc.Col(id=IDRabbit.MESSAGE_ACTION, children=[
            action_dropdown,
            html.Div(id=IDRabbit.ACTION_DESCRIPTION)
        ], width=4)),
        dbc.Row(dbc.Col(id=IDRabbit.MESSAGE_PARAMETERS, children=parameter_group, width=4)),  # parameters
        dbc.Row(dbc.Col(dbc.Button("Send", id=IDRabbit.SEND_BUTTON, color="primary", className="me-1"), width=3)),
    ])

    ###################################################################################################################
    ###################################################################################################################

    @app.callback(
        Output(IDRabbit.REPLY_STATUS, 'children'),
        Input(IDRabbit.SEND_BUTTON, 'n_clicks'),
        [State(IDRabbit.SELECT_EQUIPMENT, 'value'), State(IDRabbit.SELECT_ACTION, "value")]
    )
    def update_reply_status(n_clicks, equipment, action):
        if n_clicks is not None:
            return dbc.Alert(
                f"Message sent sent to '{equipment}' to do '{action}' at {datetime.datetime.now()}.",
                color="primary"
            )

        return ""

    @app.callback(
        Output(IDRabbit.REPLY, 'children'),
        Input(IDRabbit.REPLY_STATUS, 'children'),
        [
            State(IDRabbit.SELECT_EQUIPMENT, 'value'),
            State(IDRabbit.SELECT_ACTION, "value"),
            State({"type": "parameter", "index": ALL}, "value"),
            State({"type": "parameter_labels", "index": ALL}, "children")
        ]
    )
    def send_message_to_rabbitmq(status: str, equipment: str, action: str, parameters, labels):
        if not status:
            return [
                dbc.Placeholder(xs=6), html.Br(), dbc.Placeholder(xs=6), html.Br(),
                dbc.Placeholder(xs=6), html.Br(), dbc.Placeholder(xs=6),
            ]

        kwargs = {label: value for label, value in zip(labels, parameters)}
        try:
            message = RabbitMessageAction(
                destination="chembot." + MasterController.name,
                source="GUI",
                action="write_event",
                kwargs={"message": RabbitMessageAction(get_equipment_name(equipment), MasterController.name, action,
                                                       kwargs=kwargs), "forward": True
                        }
            )
            write_and_read_message(message)
            reply = read_message("GUI", time_out=2)
            toast = dbc.Toast(
                [html.P(str(reply['value']), className="mb-0")],
                header=f"Reply from '{equipment}' for action '{action}'.",
            )
            return html.Div([toast, html.P(str(reply), className="mb-0")])
        except Exception as e:
            return dbc.Alert('Error sending message.\n' + str(e), color="danger")

    reply_group = html.Div(
        [
            html.Br(),
            html.Br(),
            html.H3("Reply:"),
            html.Div(id=IDRabbit.REPLY_STATUS),
            html.Div(id=IDRabbit.REPLY)
        ]
    )

    return html.Div(children=[
        input_group,
        reply_group,
        html.Br(),
        html.Br()
    ])
