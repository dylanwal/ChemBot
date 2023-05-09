import logging
import queue
import threading

from chembot.configuration import config
from chembot.rabbitmq.messages import RabbitMessage, RabbitMessageAction
from chembot.rabbitmq.rabbit_core import RabbitMQConnection

logger = logging.getLogger(config.root_logger_name + ".controller")


class MasterController:
    """ Master Controller """

    def __init__(self):
        self.name = "master_controller"
        self.rabbit = RabbitMQConnection(self.name)

        self.actions = self._get_actions_list()
        self.equipment = dict()
        self._deactivate_event = threading.Event()

    def _get_actions_list(self) -> list[str]:
        actions = []
        for func in dir(self):
            if callable(getattr(self, func)) and (func.startswith("read_") or func.startswith("write_")):
                actions.append(func)

        return actions

    def _activate(self):

        logger.info(config.log_formatter(type(self).__name__, self.name, "Activated"))

    def _deactivate(self):
        self.rabbit.deactivate()
        logger.info(config.log_formatter(type(self).__name__, self.name, "Deactivated"))
        self._deactivate_event.set()

    def activate(self):
        self._activate()
        try:
            self._run()
        finally:
            self._deactivate()

    def _run(self):
        # infinite loop
        while not self._deactivate_event.wait(timeout=0.1):
            if self._check_for_errors():
                return

            # normal events
            try:
                message = self.consumer.queue.get(block=False)
                self.process_message(message)
            except queue.Empty:
                pass

    def _check_for_errors(self) -> bool:
        try:
            message = self.consumer_error.queue.get(block=False)
            self.error_handling()
            return True
        except queue.Empty:
            return False

    def process_message(self, message: RabbitMessage):
        if isinstance(message, RabbitMessageAction) and message.action in self.actions:
            try:
                func = getattr(self, message.action)
                func(message)
            except Exception as e:
                logger.exception(
                    config.log_formatter(self, self.name, "ActionError" + message.to_str())
                )
                self.error_handling()
        else:
            logger.warning("Invalid message action!!" + message.to_str())
            self.error_handling()

    def error_handling(self):
        """ Deactivate all equipment """
        # for equip in self.equipment:
        #     self.producer.send(RabbitMessageDeactivate(equip))
        self._deactivate()

    def read_equipment_status(self):
        pass


