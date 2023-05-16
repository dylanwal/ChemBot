import logging

from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

from chembot.configuration import config


logger = logging.getLogger(config.root_logger_name + ".gui")


class IDRabbit:
    SEND_BUTTON = "send_button"
    MESSAGE_DESTINATION = "message_destination"
    SELECT_DESTINATION = "select_destination"
    MESSAGE_ACTION = "message_action"
    SELECT_ACTION = "select_action"
    MESSAGE_PARAMETERS = "message_parameters"


def layout_rabbit(app: Dash) -> html.Div:
    @app.callback(Output(IDRabbit.MESSAGE_ACTION, "children"), Input(IDRabbit.SELECT_DESTINATION, "value"))
    def action_dropdown(equipment: str | None) -> html.Div:
        if equipment in gui.equipment_registry.equipment:
            equip = gui.equipment_registry.equipment[equipment]
            options = [{"label": action.name, "value": action.name} for action in equip.actions]
        else:
            options = []

        return html.Div(dbc.Select(
            id=IDRabbit.SELECT_ACTION,
            options=options
        )
        )

    # @app.callback(Output('rabbit_reply', 'children'),
    #                Input(IDRabbit.SEND_BUTTON, 'n_clicks'),
    #                State('dest', 'value'))
    # def send_message_to_rabbitmq(n_clicks, message):
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
    logger.debug(f"equip: {id(gui)}")
    equipment_dropdown = dbc.Select(
        id=IDRabbit.SELECT_DESTINATION,
        options=[{"label": equip, "value": equip} for equip in gui.equipment_registry.equipment]
    )

    input_group = html.Div(
        [
            html.Div(id=IDRabbit.MESSAGE_DESTINATION, children=[equipment_dropdown]),  # destination /equipment
            html.Div(id=IDRabbit.MESSAGE_ACTION),  # action
            html.Div(id=IDRabbit.MESSAGE_PARAMETERS),  # parameters
            dbc.Button("Send", id=IDRabbit.SEND_BUTTON, color="primary", className="me-1"),
        ]
    )

    reply_group = html.Div(
        [
            html.Br(),
            html.Br(),
            html.H3("Reply:"),
            html.Div("", id="rabbit_reply")
        ]
    )

    return html.Div(children=[
        input_group,
        reply_group,
    ])
