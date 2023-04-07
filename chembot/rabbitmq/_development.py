import threading
import queue
import logging

from chembot.rabbitmq.rabbitmq_core import RabbitMQConsumer, RabbitMQProducer


class Pump:
    root = "pump"

    def __init__(self, name: str):
        self.name = name
        self._thread = None
        self._queue = queue.Queue(maxsize=2)
        self._deactivate_event = threading.Event()

        # create at end of __init__ (needs deactivation event)
        self.rabbit_consumer = RabbitMQConsumer(topic=self.root + "." + name, parent=self)
        self.rabbit_producer = RabbitMQProducer()

    def _rabbitmq_callback(self, ch, method, properties, body):
        """ called when message received """
        self.rabbit_consumer.callback(ch, method, properties, body)

        if body == "print":
            logging.warning(self.name + ": print")
        elif body == "long":
            self._queue.put(self.name + "long")
        else:
            logging.error(self.name + f": Unrecognized message: {body}")

    def _run(self):
        """ starts equipment thread """
        self._thread = threading.Thread(target=self._main_loop)
        self._thread.start()

    def _main_loop(self):
        while not self._deactivate_event.is_set():
            try:
                action = self._queue.get(block=True, timeout=5)
            except queue.Empty:
                action = ""

            if action == "long":
                logging.warning(self.name + ": long")

            if action == "reply":
                logging.warning(self.name + ": send reply")
                self.rabbit_producer.send("pump.2", "got_relpy")

    def activate(self):
        """ Starts everything """
        self._run()
        self.rabbit_producer.activate()
        self.rabbit_consumer.activate()

    def deactivate(self):
        self.rabbit_consumer.deactivate()  # will call self._deactivate
        self.rabbit_producer.deactivate()
        self._deactivate()

    def _deactivate(self):
        self._deactivate_event.set()


class Controller:
    root = "controller"

    def __init__(self, name: str):
        self.name = name
        self._thread = None
        self._queue = queue.Queue(maxsize=2)
        self._deactivate_event = threading.Event()

        # create at end of __init__ (needs deactivation event)
        self.rabbit_producer = RabbitMQProducer()

    def activate(self):
        """ Starts everything """
        self.rabbit_producer.activate()

    def deactivate(self):
        self.rabbit_producer.deactivate()

    def send(self, message: str):
        self.rabbit_producer.send("pump.1", message)
