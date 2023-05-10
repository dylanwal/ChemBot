import logging

import pika
import pika.exceptions
logging.getLogger("pika").setLevel(logging.WARNING)

from chembot.configuration import config
from chembot.rabbitmq.messages import RabbitMessage, JSON_to_message

logger = logging.getLogger(config.root_logger_name + ".rabbitmq")


def get_rabbit_channel():
    credentials = pika.PlainCredentials(config.rabbit_username, config.rabbit_password)
    parameters = pika.ConnectionParameters(config.rabbit_host, config.rabbit_port, '/', credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.exchange_declare(exchange=config.rabbit_exchange, exchange_type='topic')

    return channel


def create_queue(channel, topic):
    result = channel.queue_declare(topic, auto_delete=True)
    channel.queue_bind(
        exchange=config.rabbit_exchange,
        queue=result.method.queue,
        routing_key=config.rabbit_exchange + "." + topic
    )


def queue_exists(channel, queue_name: str) -> bool:
    try:
        channel.queue_declare(queue=queue_name, passive=True)
        return True
    except pika.exceptions.ChannelClosed:
        return False


class RabbitMQConnection:
    def __init__(self, topic: str):
        self.topic = topic
        self.channel = get_rabbit_channel()
        create_queue(self.channel, self.topic)
        self.queue = self.channel.queue_declare(queue=topic, passive=True)
        logger.debug(config.log_formatter(self, self.topic, "Rabbit connection established."))

    @property
    def messages_in_queue(self) -> int:
        return self.queue.method.message_count

    def queue_exists(self, queue_name: str) -> bool:
        return queue_exists(self.channel, queue_name)

    def consume(self, timeout: int | float = 0.1) -> RabbitMessage | None:
        for method, properties, body in self.channel.consume(queue=self.topic, auto_ack=True, inactivity_timeout=timeout):
            if body is None:
                return None

            return self._process_message(body.decode(config.encoding))

    def _process_message(self, body: str) -> RabbitMessage | None:
        try:
            message = JSON_to_message(body)
            logger.debug(config.log_formatter(self, self.topic, "Message received:" + message.to_str()))
            return message
        except Exception as e:
            logger.exception(config.log_formatter(self, self.topic, "Received message caused Exception."))

    def send(self, message: RabbitMessage):
        if not queue_exists(self.channel, message.destination):
            logger.error(config.log_formatter(self, self.topic, "Queue does not exist yet:" + message.destination))
            raise ValueError("Queue does not exist yet:" + message.destination)

        result = self.channel.basic_publish(
            exchange=config.rabbit_exchange,
            routing_key=config.rabbit_exchange + "." + message.destination,
            body=message.to_JSON().encode(config.encoding),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        if result:
            logger.debug(config.log_formatter(self, self.topic, "Message sent:" + message.to_str()))
        else:
            logger.error(config.log_formatter(self, self.topic, "Message not sent:" + message.to_str()))
            raise ValueError()

    def deactivate(self):
        self.channel.basic_cancel(self.topic)
