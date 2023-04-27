
import logging
import threading
import queue
import time

import pika
import pika.exceptions
logging.getLogger("pika").setLevel(logging.WARNING)

from chembot.configuration import config
from chembot.rabbitmq.messages import RabbitMessage, RabbitMessageError

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
        queue = channel.queue_declare(queue=queue_name, passive=True)
        return True
    except pika.exceptions.ChannelClosed:
        return False


class RabbitMQConsumer:

    def __init__(self, topic: str):
        self.topic = topic
        self.channel = get_rabbit_channel()
        create_queue(self.channel, self.topic)

        self.thread: threading.Thread = threading.Thread(target=self._run)
        self.queue: queue.Queue[RabbitMessage] = queue.Queue(maxsize=1)

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
        self._add_message_to_queue(message)
        self.queue.put(message)
        logger.debug(config.log_formatter(type(self).__name__, self.topic, "Message received:" + message.to_str()))

    def _add_message_to_queue(self, message: RabbitMessage):
        for i in range(config.rabbit_queue_timeout * 10):
            if not self.queue.full():
                self.queue.put(message)
                return

            time.sleep(0.1)

        # raise timeout error if queue not emptied within timeout limit
        self.channel.queue_declare("error")
        error_message = RabbitMessageError(message.destination, "Queue Timeout Error.")
        self.channel.basic_publish(
            exchange=config.rabbit_exchange,
            routing_key="error",
            body=error_message.to_JSON().encode(config.encoding),
            properties=pika.BasicProperties(delivery_mode=2)
        )

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
        if not queue_exists(self._channel, message.destination):
            logger.exception(
                config.log_formatter(self, self.name, "Queue does not exist yet:" + message.to_str())
            )
            raise ValueError()

        result = self._channel.basic_publish(
            exchange=config.rabbit_exchange,
            routing_key=config.rabbit_exchange + "." + message.destination,
            body=message.to_JSON().encode(config.encoding),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        logger.debug(config.log_formatter(self, self.name, "Message sent:" + message.to_str()))


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

    def send_error(self, message: str):
        self.send(RabbitMessageError(self.consumer.topic, message))
