import time
import logging
from typing import Protocol

from chembot.configuration import config
from chembot.rabbitmq.messages import RabbitMessage, RabbitMessageReply, RabbitMessageError
from chembot.rabbitmq.rabbit_core import RabbitMQConnection

logger = logging.getLogger(config.root_logger_name + ".watchdog")


class WatchdogParent(Protocol):
    name = None
    rabbit: RabbitMQConnection = None


class WatchdogEvent:
    def __init__(self, id_: int, delay: int | float, expect_reply: str | None = None, reply_callback: callable = None):
        self.id_ = id_
        self.delay = delay
        self.expect_reply = expect_reply
        self.reply_callback = reply_callback

        self.warn_time = time.time() + delay

    def __str__(self):
        return f"{self.id_}: {self.warn_time}"


class RabbitWatchdog:

    def __init__(self, parent: WatchdogParent):
        self.parent = parent
        self.watchdogs: dict[int, WatchdogEvent] = {}

    def __contains__(self, item: int) -> bool:
        return item in self.watchdogs.keys()

    def set_watchdog(self, message: RabbitMessage, delay: int | float,
                     expected_reply=None, reply_callback: callable = None
                     ):
        """
        Parameters
        ----------
        message:
            message you want to set a watch dog for
        delay:
            time to wait till activate watchdog
        expected_reply:
            expected reply value
        reply_callback:
            function to call upon receiving the reply.

        """
        self.watchdogs[message.id_] = WatchdogEvent(message.id_, delay, expected_reply, reply_callback)

    def deactivate_watchdog(self, message: RabbitMessageReply):
        if message.id_reply not in self.watchdogs:
            logger.exception(f"Reply id({message.id_reply}) not in watchdog list for parent '{self.parent.name}'.")
            return

        watchdog = self.watchdogs[message.id_reply]

        if watchdog.expect_reply is not None and message.value != watchdog.expect_reply:
            raise ValueError(f"Reply message has wrong value. message_id: ({message.id_}) \nvalue: {message.value}"
                             f"\nexpected value: {watchdog.expect_reply}")

        if watchdog.reply_callback:
            watchdog.reply_callback(message)

        del self.watchdogs[message.id_reply]

    def check_watchdogs(self):
        now = time.time()
        del_watchdog = []
        for id_, watchdog in self.watchdogs.items():
            if now > watchdog.warn_time:
                # trigger watchdog
                del_watchdog.append(id_)
                self.parent.rabbit.send(
                    RabbitMessageError(self.parent.name, f"Watchdog triggered for message {watchdog}")
                )

        # delete triggered watchdogs
        for id_ in del_watchdog:
            del self.watchdogs[id_]
