"""

Extension to rabbit_http.py to handle send/receiving RabbitMessages.


"""

import time
import logging

from chembot.configuration import config
from chembot.rabbitmq.messages import RabbitMessage, JSON_to_class
from chembot.rabbitmq.rabbit_http import publish, get

logger = logging.getLogger(config.root_logger_name + ".rabbitmq")


def write_message(message: RabbitMessage):
    """ assumes a topic exchange """
    publish(message.destination, message.to_JSON())
    logger.debug(config.log_formatter("RabbitMQConnection", "http", "Message sent:" + message.to_str()))


def read_message(queue: str, time_out: float = 1, create: bool = False):
    time_out = time.time() + time_out

    while time.time() < time_out:  # repeatedly check for messages in queue till timeout reached.
        reply = get(queue)[0]

        if reply:
            logger.debug(config.log_formatter("RabbitMQConnection", "http", "Message received:"
                                              + str(reply)[:min([25, len(reply)])]))
            if create:
                return JSON_to_class(reply)
            return reply

    raise ValueError(f"Timeout error on queue: {queue}")


def write_and_read_message(message: RabbitMessage, timeout: float = 1):
    write_message(message)
    return read_message(message.source, timeout)
