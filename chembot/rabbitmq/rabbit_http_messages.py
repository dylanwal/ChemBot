"""

Extension to rabbit_http.py to handle send/receiving RabbitMessages.


"""

import time
import logging
import pickle

from chembot.configuration import config
from chembot.rabbitmq.messages import RabbitMessage
from chembot.rabbitmq.rabbit_http import publish, get

logger = logging.getLogger(config.root_logger_name + ".rabbitmq")


def write_message(message: RabbitMessage):
    """ assumes a topic exchange """
    publish(message.destination, message.to_bytes())
    logger.debug(config.log_formatter("RabbitMQConnection", "http", "Message sent:" + message.to_str()))


def read_message(queue: str, time_out: float = 1, create: bool = False) -> str | bytes:
    time_out = time.time() + time_out

    while time.time() < time_out:  # repeatedly check for messages in queue till timeout reached.
        reply = get(queue)

        if reply:
            reply = reply[0]
            logger.debug(config.log_formatter("RabbitMQConnection", "http", "Message received:\n\t"
                                              + str(reply)[:min([100, len(str(reply))])]))
            if create:
                return pickle.loads(reply)
            return reply

    raise ValueError(f"Timeout error on queue: {queue}")


def write_and_read_message(message: RabbitMessage, timeout: float = 1) -> str | bytes:
    write_message(message)
    return read_message(message.source, timeout)
