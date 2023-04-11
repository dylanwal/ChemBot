import logging
import queue
import time

from chembot.configuration import config
from chembot.rabbitmq.core import RabbitMQProducer, RabbitMQConsumer, RabbitMessage

logger = logging.getLogger(config.root_logger_name + ".controller")


class ControllerManual:
    """ Controller Manual """

    def __init__(self):
        self.name = "controller"
        self.producer = RabbitMQProducer(self.name)
        self.consumer = RabbitMQConsumer(self.name)
        self.consumer_error = RabbitMQConsumer("error")
        self.consumer_status = RabbitMQConsumer("status")
        self.consumer_help = RabbitMQConsumer("help")
        self.consumer_actions = RabbitMQConsumer("actions")
        self.consumer_details = RabbitMQConsumer("details")

    def _activate(self):
        self.producer.activate()
        self.consumer.activate()
        self.consumer_error.activate()
        self.consumer_status.activate()
        self.consumer_help.activate()
        self.consumer_actions.activate()
        self.consumer_details.activate()
        logger.info(config.log_formatter(type(self).__name__, self.name, "Activated"))

    def _deactivate(self):
        self.consumer.deactivate()
        self.consumer_error.deactivate()
        self.consumer_status.deactivate()
        self.consumer_help.deactivate()
        self.consumer_actions.deactivate()
        self.consumer_details.deactivate()
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
