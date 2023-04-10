from __future__ import annotations

import abc
import logging
import threading
import queue
import json

import pika
logging.getLogger("pika").setLevel(logging.WARNING)

from chembot.configuration import config

logger = logging.getLogger(config.root_logger_name + "rabbitmq")


def get_rabbit_channel():
    credentials = pika.PlainCredentials(config.rabbit_username, config.rabbit_password)
    parameters = pika.ConnectionParameters(config.rabbit_host, config.rabbit_port, '/', credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.exchange_declare(exchange=config.rabbit_exchange, exchange_type='topic')

    return channel


class RabbitMessage:
    def __init__(self, destination: str, source: str, action: str, value, parameters: dict = None):
        self.destination = destination
        self.source = source
        self.action = action
        self.value = value
        self.parameters = parameters

    def to_JSON(self) -> str:  # noqa
        return json.dumps(self, default=lambda x: x.__dict__)

    def to_str(self) -> str:
        return f"\n\t{self.source} -> {self.destination} " \
                 f"\n\taction: {self.action}" \
                 f"\n\tvalue: {self.value}"

    @classmethod
    def from_JSON(cls, message: str) -> RabbitMessage:  # noqa
        message = json.loads(message)
        return RabbitMessage(**message)


class RabbitMQConsumer:

    def __init__(self, topic: str):
        self.topic = topic
        self.channel = get_rabbit_channel()
        self.channel.queue_declare(self.topic)

        self.thread: threading.Thread = threading.Thread(target=self._run)
        self.queue: queue.Queue[RabbitMessage] = queue.Queue(maxsize=2)

    def activate(self):
        self.thread.start()
        logger.info(f"Start listening on: {self.topic}")

    def _run(self):
        self.channel.basic_consume(
            queue=self.topic,
            on_message_callback=self._callback,
            auto_ack=True,
            consumer_tag=self.topic
        )
        self.channel.start_consuming()

    def _callback(self, ch, method, properties, body):
        message = RabbitMessage.from_JSON(body)
        logger.debug("Message received:" + message.to_str())
        self.queue.put(message)

    def deactivate(self):
        self.channel.basic_cancel(self.topic)
        self.thread.join()


class RabbitMQProducer:
    def __init__(self):
        self._channel = None

    def _connect(self):
        self._channel = get_rabbit_channel()

    def activate(self):
        self._connect()

    def send(self, message: RabbitMessage):
        if not self._channel.queue_declare(message.destination, passive=True):
            # no queue for topic
            raise ValueError("No Topic")

        logger.debug("Message sent:" + message.to_str())
        self._channel.basic_publish(
            exchange=config.rabbit_exchange,
            routing_key=message.destination,
            body=message.to_JSON()
        )


class RabbitCommunication:

    def __init__(self, topic: str):
        self.producer = RabbitMQProducer()
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


class RabbitEquipment(abc.ABC):
    def __init__(self, topic: str):
        self.topic = topic
        self.rabbit = RabbitCommunication(topic)
        self.actions = [func for func in dir(self) if callable(getattr(self, func)) and func.startswith("action_")]

    def activate(self):
        self.rabbit.activate()
        try:
            self._run()
        except KeyboardInterrupt:
            logger.warning("Keyboard Interrupt")
        finally:
            self.action_deactivate()

    def _run(self):
        # infinite loop
        while True:
            try:
                message = self.rabbit.queue.get(block=True, timeout=5)

                if message.action in self.actions:
                    try:
                        func = getattr(self, "action_" + message.action)
                        func(message)
                    except Exception as e:
                        logging.warning("ActionError" + message.to_str())
                        self.rabbit.send_error("ActionError", message.to_str())
                else:
                    logging.warning("Invalid message action!!" + message.to_str())
                    self.rabbit.send_error("InvalidMessage", message.to_str())

            except queue.Empty:
                pass

    def action_status(self):
        message = RabbitMessage("status", self.topic, "update", self.equipment_config.state)
        self.rabbit.send(message)

    def action_help(self):
        message = RabbitMessage("help", self.topic, "help", self.__doc__)
        self.rabbit.send(message)

    def action_actions(self, actions: list[str, ...]):
        message = RabbitMessage("actions", self.topic, "actions", actions)
        self.rabbit.send(message)

    def action_details(self):
        message = RabbitMessage("details", self.topic, "actions", self._get_details())
        self.rabbit.send(message)

    @abc.abstractmethod
    def _get_details(self) -> dict:
        ...

    def action_deactivate(self):
        self.rabbit.deactivate()
        logger.info("Shutdown successful.")
