import logging

from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

from chembot.configuration import config
from chembot.gui.gui_data import IDDataStore
from chembot.rabbitmq.messages import JSON_to_class
from chembot.master_controller.registry import EquipmentRegistry
from chembot.equipment.equipment_interface import ActionParameter, EquipmentInterface, NotDefinedParameter, \
    NumericalRange, CategoricalRange

logger = logging.getLogger(config.root_logger_name + ".gui")


class IDRabbit:
    SEND_BUTTON = "send_button"
    MESSAGE_DESTINATION = "message_destination"
    SELECT_EQUIPMENT = "select_destination"
    MESSAGE_ACTION = "message_action"
    SELECT_ACTION = "select_action"
    MESSAGE_PARAMETERS = "message_parameters"
    PARAMETERS_GROUP = "parameters_group"
    REPLY = "reply"


def get_parameter_div(param: ActionParameter) -> dbc.InputGroup:
    children = [dbc.InputGroupText(param.name)]
    if param.types == "str":
        if param.default is NotDefinedParameter:
            text = "text"
        else:
            text = param.default
        children.append(dbc.Input(text))

    if param.types == "str" and param.range_:  # with options
        if param.default is NotDefinedParameter:
            value = None
        else:
            value = param.default
            range_: CategoricalRange = param.range_
        children.append(dbc.Select(id=IDRabbit.SELECT_EQUIPMENT, options=range_.options, value=value))

    if param.types == "int" or param.types == "float":
        children.append(dbc.Input("value", type="number"))
        children.append(dbc.InputGroupText(param.unit))
        if param.range_ is not None:
            children.append(dbc.InputGroupText('range :' + str(param.range_)))

    if param.types == "bool":
        children.append(dbc.Switch(value=False))

    return dbc.InputGroup(children)


def get_equipment_name(text: str) -> str:
    return text.split(" ")[0]


def get_equipment(text: str, data: dict[str, object]) -> EquipmentInterface:
    equipment_name = get_equipment_name(text)
    equipment_registry: EquipmentRegistry = JSON_to_class(data)
    return equipment_registry.equipment[equipment_name]


def layout_rabbit(app: Dash) -> html.Div:
    @app.callback(
        Output(IDRabbit.SELECT_EQUIPMENT, "options"),
        [Input(IDDataStore.EQUIPMENT_REGISTRY, "data")],
    )
    def update_equipment_dropdown(data: dict[str, object]) -> list[str]:
        equipment_registry: EquipmentRegistry = JSON_to_class(data)
        equipment = [f"{equip.name} ({equip.class_})" for equip in equipment_registry.equipment.values()]
        return equipment

    @app.callback(
        Output(IDRabbit.SELECT_ACTION, "options"),
        Input(IDRabbit.SELECT_EQUIPMENT, "value"),
        State(IDDataStore.EQUIPMENT_REGISTRY, "data")
    )
    def update_action_dropdown(equipment: str | None, data: dict[str, object]) -> list[str]:
        if equipment:
            equipment = get_equipment(equipment, data)
            return [action.name for action in equipment.actions]
        return []

    @app.callback(
        Output(IDRabbit.PARAMETERS_GROUP, "children"),
        Input(IDRabbit.SELECT_ACTION, "value"),
        [State(IDDataStore.EQUIPMENT_REGISTRY, "data"), State(IDRabbit.SELECT_EQUIPMENT, "value")]
    )
    def update_parameters_group(action: str, data: dict[str, object], equipment: str | None) -> list:
        if equipment is None:
            return []

        parameter_components = []
        equipment = get_equipment(equipment, data)
        action = equipment.get_action(action)
        if action.inputs:
            for param in action.inputs:
                parameter_components.append(get_parameter_div(param))

        return parameter_components

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
        dbc.Row(dbc.Col(id=IDRabbit.MESSAGE_DESTINATION, children=[equipment_dropdown], width=3)),
        dbc.Row(dbc.Col(id=IDRabbit.MESSAGE_ACTION, children=[action_dropdown], width=3)),  # action
        dbc.Row(dbc.Col(id=IDRabbit.MESSAGE_PARAMETERS, children=parameter_group, width=3)),  # parameters
        dbc.Row(dbc.Col(dbc.Button("Send", id=IDRabbit.SEND_BUTTON, color="primary", className="me-1"), width=3)),
    ])

######################################################################################################################
######################################################################################################################

    # @app.callback(
    #     Output(IDRabbit.REPLY, 'children'),
    #                Input(IDRabbit.SEND_BUTTON, 'n_clicks'),
    #                [State(IDRabbit.SELECT_EQUIPMENT, 'value'), State(IDRabbit.SELECT_ACTION, "value")]
    #               )
    # def send_message_to_rabbitmq(n_clicks, message) -> str:
    #     if n_clicks is not None:
    #         try:
    #             # connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    #             # channel = connection.channel()
    #             # channel.queue_declare(queue='my_queue')
    #             # channel.basic_publish(exchange='', routing_key='my_queue', body=message)
    #             # connection.close()
    #             return html.Div(f'Message sent: {message}')
    #         except:
    #             return html.Div('Error: Could not connect to RabbitMQ')
    #     else:
    #         return html.Div()

    # equipment_dropdown = dbc.Select(
    #     id=IDRabbit.SELECT_EQUIPMENT,
    #     options=[{"label": equip, "value": equip} for equip in gui.equipment_registry.equipment]
    # )

    reply_group = html.Div(
        [
            html.Br(),
            html.Br(),
            html.H3("Reply:"),
            html.P(id=IDRabbit.REPLY)
        ]
    )

    return html.Div(children=[
        input_group,
        reply_group,
    ])
