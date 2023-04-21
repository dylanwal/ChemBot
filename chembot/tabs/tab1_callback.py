from dash import html

from tabs.main import app
from dash.dependencies import Input, Output, State


@app.callback(Output('send-message-status', 'children'),
              Input('send-button', 'n_clicks'),
              State('message-input', 'value'))
def send_message_to_rabbitmq(n_clicks, message):
    if n_clicks > 0:
        try:
            # connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            # channel = connection.channel()
            # channel.queue_declare(queue='my_queue')
            # channel.basic_publish(exchange='', routing_key='my_queue', body=message)
            # connection.close()
            return html.Div('Message sent to RabbitMQ')
        except:
            return html.Div('Error: Could not connect to RabbitMQ')
    else:
        return html.Div()


