import logging
import queue
import time

from chembot.configuration import config
from chembot.rabbitmq.rabbit_core import RabbitMQConnection, RabbitMessage

logger = logging.getLogger(config.root_logger_name + ".controller")


class ControllerManual:
    """ Controller Manual """

    def __init__(self):
        self.name = "controller"
        self.rabbit = RabbitMQConnection(self.name)

    def _activate(self):
        logger.info(config.log_formatter(type(self).__name__, self.name, "Activated"))

    def _deactivate(self):
        self.rabbit.deactivate()
        logger.info(config.log_formatter(type(self).__name__, self.name, "Deactivated"))

    def activate(self):
        self._activate()
        try:
            self._run()
        finally:
            self._deactivate()

    def _run(self):
        # infinite loop
        while True:
            print()
            print("Send new command: or 'skip':")
            input_ = input("\tdestination, action, value").replace(" ", "")
            values = input_.split(",")
            if len(values) == 3:
                message = RabbitMessage(values[0], "controller", values[1], values[2])
                self.producer.send(message)

            time.sleep(0.3)
            try:
                message = self.consumer.queue.get(block=True, timeout=0.2)
                print("consumer: ", message)
            except queue.Empty:
                pass

            try:
                message = self.consumer_status.queue.get(block=True, timeout=0.2)
                print("consumer_status: ", message)
            except queue.Empty:
                pass

            try:
                message = self.consumer_help.queue.get(block=True, timeout=0.2)
                print("consumer_help: ", message)
            except queue.Empty:
                pass

            try:
                message = self.consumer_actions.queue.get(block=True, timeout=0.2)
                print("consumer_actions: ", message)
            except queue.Empty:
                pass

            try:
                message = self.consumer_details.queue.get(block=True, timeout=0.2)
                print("consumer_details: ", message)
            except queue.Empty:
                pass

            try:
                message = self.consumer_error.queue.get(block=True, timeout=0.2)
                print("consumer_error: ", message)
            except queue.Empty:
                pass
