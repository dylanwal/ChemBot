import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

dash.register_page(__name__)

input_group = html.Div(
    [
        html.H3("Send:"),
        dbc.InputGroup(
            [dbc.InputGroupText("destination"), dbc.Input(id="dest")],
            className="mb-1", style={"width": "20%"},
        ),
        dbc.InputGroup(
            [dbc.InputGroupText("action"), dbc.Input()],
            className="mb-1", style={"width": "20%"}
        ),
        dbc.InputGroup(
            [dbc.InputGroupText("value"), dbc.Input()],
            className="mb-1", style={"width": "20%"}
        ),
        dbc.Button("Send", id="rabbit_send_button", color="primary", className="me-1"),
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

layout = html.Div(children=[
    input_group,
    reply_group,
])


@dash.callback(Output('rabbit_reply', 'children'),
               Input('rabbit_send_button', 'n_clicks'),
               State('dest', 'value'))
def send_message_to_rabbitmq(n_clicks, message):
    if n_clicks is not None:
        try:
            # connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            # channel = connection.channel()
            # channel.queue_declare(queue='my_queue')
            # channel.basic_publish(exchange='', routing_key='my_queue', body=message)
            # connection.close()
            return html.Div(f'Message sent: {message}')
        except:
            return html.Div('Error: Could not connect to RabbitMQ')
    else:
        return html.Div()
