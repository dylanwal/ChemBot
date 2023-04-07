"""
Installation
1) Open Powershell as Administrator
2) Install chocolatey (https://chocolatey.org/install)
3) Install RabbitMQ `choco install rabbitmq`
4) Server starts up automatically on install

RabbitMQ
    # Navigate to location of server files
    'cd C:\Program Files\RabbitMQ Server\rabbitmq_server-3.11.13\sbin'  # version may be different

    # start server
    `.\rabbitmq-server.bat -detached`

    # stop server
    `.\rabbitmqctl.bat stop`

    # check server status
    `.\rabbitmqctl.bat status`


# checking server
http://localhost:15672/
Username: guest
Password: guest

"""
import logging
import os
import sys
import threading
from typing import Protocol

import pika


class EquipmentProtocol(Protocol):
    _deactivate_event = None

    def _rabbitmq_callback(self, ch, method, properties, body):
        pass

    def deactivate(self):
        pass


class RabbitMQConsumer:

    def __init__(self, topic: str, parent: EquipmentProtocol,
                 host='localhost', port=5672, username='guest', password='guest', exchange='chembot'):
        self.topic = topic
        self.parent = parent
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._exchange = exchange
        self._connection = None
        self._channel = None
        self._deactivate_event: threading.Event = parent._deactivate_event

    def _connect(self):
        credentials = pika.PlainCredentials(self._username, self._password)
        parameters = pika.ConnectionParameters(self._host, self._port, '/', credentials)
        self._connection = pika.BlockingConnection(parameters)
        self._channel = self._connection.channel()
        self._channel.exchange_declare(exchange=self._exchange, exchange_type='topic')
        self._channel.queue_declare(self.topic)

    def activate(self):
        self._connect()
        self._run()

    def deactivate(self):
        self._connection.close()

    def _run(self):
        try:
            self._consume()
        except KeyboardInterrupt:
            pass

        # catch interrupt or close command and handle it gracefully
        self.parent.deactivate()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)  # noqa

    def _consume(self):
        logging.warning("listening")
        while not self._deactivate_event.is_set():
            self._channel.basic_consume(
                queue=self.topic,
                on_message_callback=self.parent._rabbitmq_callback,
                auto_ack=True,
            )

    def callback(self, ch, method, properties, body):
        if body == "deactivate":
            self._deactivate_event.set()


class RabbitMQProducer:
    def __init__(self,  host='localhost', port=5672, username='guest', password='guest', exchange='chembot'):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._exchange = exchange
        self._connection = None
        self._channel = None

    def _connect(self):
        credentials = pika.PlainCredentials(self._username, self._password)
        parameters = pika.ConnectionParameters(self._host, self._port, '/', credentials)
        self._connection = pika.BlockingConnection(parameters)
        self._channel = self._connection.channel()
        self._channel.exchange_declare(exchange=self._exchange, exchange_type='topic')

    def activate(self):
        self._connect()

    def send(self, topic: str, body: str):
        if not self._channel.queue_declare(topic, passive=True):
            # no queue for topic
            # handle error
            raise ValueError("No Topic")

        self._channel.basic_publish(exchange=self._exchange, routing_key=topic, body=body)

    def deactivate(self):
        self._connection.close()
