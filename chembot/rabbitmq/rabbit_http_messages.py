"""

Extension to rabbit_http.py to handle send/receiving RabbitMessages.


"""
import json
import time
import logging
import pickle

from chembot.configuration import config
from chembot.rabbitmq.messages import RabbitMessage, RabbitMessageReply
from chembot.rabbitmq.rabbit_http import publish, get

logger = logging.getLogger(config.root_logger_name + ".rabbitmq")


def write_message(message: RabbitMessage):
    """ assumes a topic exchange """
    publish(message.destination, message.to_bytes())
    logger.debug(config.log_formatter("RabbitMQConnection", "http", "Message sent:" + message.to_str()))


def read_message(queue: str, time_out: float = 1) -> str | bytes:
    time_out = time.time() + time_out

    while time.time() < time_out:  # repeatedly check for messages in queue till timeout reached.
        reply = get(queue)  # RabbitMessage in bytes or JSON

        if reply:
            reply = reply[0]
            logger.debug(config.log_formatter("RabbitMQConnection", "http", "Message received:\n\t"
                                              + str(reply)[:min([100, len(str(reply))])]))
            return reply

    raise ValueError(f"Timeout error on queue: {queue}")


def re_create_message(message: str | bytes) -> RabbitMessageReply:
    # str -> json
    # bytes -> pickled python object
    if isinstance(message, bytes):
        return pickle.loads(message)
    return json.loads(message)


def write_and_read_message(message: RabbitMessage, time_out: float = 1) -> str | bytes:
    write_message(message)
    return read_message(message.source, time_out)


def read_create_message(queue: str, time_out: float = 1) -> RabbitMessageReply:
    reply = read_message(queue, time_out)
    return re_create_message(reply)


def write_read_create_message(message: RabbitMessage, time_out: float = 1) -> RabbitMessageReply:
    write_message(message)
    reply = read_message(message.source, time_out)
    return re_create_message(reply)
