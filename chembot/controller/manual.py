import logging
import queue
import time

from chembot.configuration import config
from chembot.rabbitmq.rabbitmq_core import RabbitMQProducer, RabbitMQConsumer, RabbitMessage

logger = logging.getLogger(config.root_logger_name + "controller")


class Controller:
    def __init__(self):
        self.producer = RabbitMQProducer()
        self.consumer = RabbitMQConsumer('controller')
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

    def _deactivate(self):
        self.consumer.deactivate()
        self.consumer_error.deactivate()
        self.consumer_status.deactivate()
        self.consumer_help.deactivate()
        self.consumer_actions.deactivate()
        self.consumer_details.deactivate()

    def activate(self):
        logger.info(f"Controller activated.")
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
            destination = input("\tdestination: ")
            if destination == "skip":
                action = input("\taction: ")
                value = input("\tvalue: ")
                message = RabbitMessage(destination, "controller", action, value)
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
