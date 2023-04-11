
import logging
import threading
import queue

import pika
import pika.exceptions
logging.getLogger("pika").setLevel(logging.WARNING)

from chembot.configuration import config
from chembot.rabbitmq.message import RabbitMessage

logger = logging.getLogger(config.root_logger_name + ".rabbitmq")


def get_rabbit_channel():
    credentials = pika.PlainCredentials(config.rabbit_username, config.rabbit_password)
    parameters = pika.ConnectionParameters(config.rabbit_host, config.rabbit_port, '/', credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.exchange_declare(exchange=config.rabbit_exchange, exchange_type='topic')

    return channel


class RabbitMQConsumer:

    def __init__(self, topic: str):
        self.topic = topic
        self.channel = get_rabbit_channel()
        result = self.channel.queue_declare(self.topic, auto_delete=True)
        self.channel.queue_bind(exchange=config.rabbit_exchange, queue=result.method.queue,
                                routing_key=config.rabbit_exchange + "." + topic)

        self.thread: threading.Thread = threading.Thread(target=self._run)
        self.queue: queue.Queue[RabbitMessage] = queue.Queue(maxsize=2)

    def activate(self):
        self.thread.start()

    def _run(self):
        """ This is the loop in a thread """
        logger.debug(config.log_formatter(type(self).__name__, self.topic, "Started listening"))
        self.channel.basic_consume(
            queue=self.topic,
            on_message_callback=self._callback,
            # auto_ack=True,
            consumer_tag=self.topic
        )
        self.channel.start_consuming()
        logger.debug(config.log_formatter(type(self).__name__, self.topic, "Stop listening"))

    def _callback(self, ch, method, properties, body):
        """ called every time a message is received. """
        try:
            message = RabbitMessage.from_JSON(body)
        except Exception as e:
            logger.exception(
                config.log_formatter(type(self).__name__, self.topic, "Received message caused Exception.")
            )
            return

        self.queue.put(message)
        logger.debug(config.log_formatter(type(self).__name__, self.topic, "Message received:" + message.to_str()))

    def deactivate(self):
        self.channel.basic_cancel(self.topic)
        self.thread.join()


class RabbitMQProducer:
    def __init__(self, name: str):
        self.name = name
        self._channel = get_rabbit_channel()

    def activate(self):
        pass

    def send(self, message: RabbitMessage):
        # check if queue exists
        try:
            self._channel.queue_declare(message.destination, passive=True)
        except pika.exceptions.ChannelClosedByBroker:
            logger.error(
                config.log_formatter(type(self).__name__, self.name, "Queue does not exist yet:" + message.to_str())
            )
            raise ValueError()

        result = self._channel.basic_publish(
            exchange=config.rabbit_exchange,
            routing_key=config.rabbit_exchange + "." + message.destination,
            body=message.to_JSON(),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        logger.debug(config.log_formatter(type(self).__name__, self.name, "Message sent:" + message.to_str()))


class RabbitCommunication:
    def __init__(self, topic: str):
        self.producer = RabbitMQProducer(topic)
        self.consumer = RabbitMQConsumer(topic)

    @property
    def queue(self) -> queue.Queue[RabbitMessage]:
        return self.consumer.queue

    def activate(self):
        self.producer.activate()
        self.consumer.activate()

    def deactivate(self):
        self.consumer.deactivate()

    def send(self, message: RabbitMessage):
        self.producer.send(message)

    def send_error(self, action, message: str):
        message = RabbitMessage("error", self.consumer.topic, action, message)
        self.producer.send(message)
