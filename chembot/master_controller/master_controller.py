import logging
import threading

from chembot.configuration import config
from chembot.rabbitmq.messages import RabbitMessage, RabbitMessageAction, RabbitMessageCritical, RabbitMessageError
from chembot.rabbitmq.rabbit_core import RabbitMQConnection
from chembot.rabbitmq.watchdog import RabbitWatchdog
from chembot.master_controller.registry import EquipmentRegistry

logger = logging.getLogger(config.root_logger_name + ".controller")


class MasterController:
    """ Master Controller """

    def __init__(self):
        self.name = "master_controller"
        self.rabbit = RabbitMQConnection(self.name)
        self.watchdog = RabbitWatchdog(self)
        self.registry = EquipmentRegistry()
        self._deactivate_event = threading.Event()

    def _deactivate(self):
        self.rabbit.deactivate()
        logger.info(config.log_formatter(self, self.name, "Deactivated"))
        self._deactivate_event.set()

    def activate(self):
        logger.info(config.log_formatter(self, self.name, "Activated"))
        try:
            self._run()
        finally:
            self._deactivate()

    def _run(self):
        # infinite loop
        while not self._deactivate_event.wait(timeout=0.01):
            self.watchdog.check_watchdogs()
            message = self.rabbit.consume()
            if message is None:
                continue

            self._process_message(message)

    def _process_message(self, message: RabbitMessage):
        if isinstance(message, RabbitMessageCritical):
            self._deactivate_event.set()

        elif isinstance(message, RabbitMessageError):
            self._deactivate_event.set()

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


