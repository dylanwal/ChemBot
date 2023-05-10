import time
from typing import Protocol

from chembot.rabbitmq.messages import RabbitMessageAction, RabbitMessageReply, RabbitMessageError
from chembot.rabbitmq.rabbit_core import RabbitMQConnection


class WatchdogParent(Protocol):
    name = None
    rabbit: RabbitMQConnection = None


class RabbitWatchdog:

    def __init__(self, parent: WatchdogParent):
        self.parent = parent
        self.watchdogs = {}

    def set_watchdog(self, message: RabbitMessageAction, delay: int | float):
        """
        Parameters
        ----------
        message:
            message you want to set a watch dog for
        delay:
            time to wait till activate watchdog

        """
        self.watchdogs[message.id_] = time.time() + delay

    def deactivate_watchdog(self, message: RabbitMessageReply):
        if message.id_reply not in self.watchdogs:
            raise ValueError("Reply id not in watchdog list.")

        del self.watchdogs[message.id_reply]

    def check_watchdogs(self):
        now = time.time()
        for id_, time_ in self.watchdogs:
            if now > time_:
                # trigger watchdog
                self.parent.rabbit.send(RabbitMessageError(self.parent.name, f"Watchdog triggered for message {id_}"))
