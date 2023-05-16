import logging

from chembot.configuration import config
from chembot.utils.class_building import get_actions_list
from chembot.rabbitmq.messages import RabbitMessage, RabbitMessageAction, RabbitMessageCritical, RabbitMessageError, \
    RabbitMessageRegister, RabbitMessageReply
from chembot.rabbitmq.rabbit_core import RabbitMQConnection
from chembot.rabbitmq.watchdog import RabbitWatchdog
from chembot.master_controller.registry import EquipmentRegistry

logger = logging.getLogger(config.root_logger_name + ".controller")


class MasterController:
    """ Master Controller """
    name = "master_controller"
    pulse = 0.01  # time of each loop in seconds

    def __init__(self):
        self.actions = get_actions_list(self)
        self.rabbit = RabbitMQConnection(self.name)
        self.watchdog = RabbitWatchdog(self)
        self.registry = EquipmentRegistry()
        self._deactivate_event = False

    def _deactivate(self):
        self.rabbit.deactivate()
        logger.info(config.log_formatter(self, self.name, "Deactivated"))
        self._deactivate_event = True

    def activate(self):
        logger.info(config.log_formatter(self, self.name, "Activated"))
        try:
            self._run()
        finally:
            self._deactivate()

    def _run(self):
        # infinite loop
        while True:
            self.watchdog.check_watchdogs()
            message = self.rabbit.consume(self.pulse)
            if message:
                self._process_message(message)
            if self._deactivate_event:
                break

    def _process_message(self, message: RabbitMessage):
        if isinstance(message, RabbitMessageCritical):
            self._error_handling()
            self._deactivate_event = True

        elif isinstance(message, RabbitMessageError):
            self._error_handling()
            self._deactivate_event = True

        elif isinstance(message, RabbitMessageRegister):
            self.registry.register(message)
            self.rabbit.send(RabbitMessageReply.create_reply(message, None))

        elif isinstance(message, RabbitMessageAction):
            self._execute_action(message)

        elif isinstance(message, RabbitMessageReply):
            self.watchdog.deactivate_watchdog(message)

        else:
            logger.warning("Invalid message!!" + message.to_str())
            self.rabbit.send(RabbitMessageError(self.name, f"InvalidMessage: {message.to_str()}"))

    def _execute_action(self, message):
        if message.action not in self.actions:
            logger.warning("Invalid action!!" + message.to_str())
            self.rabbit.send(RabbitMessageError(self.name, f"Invalid action: {message.to_str()}"))

        try:
            func = getattr(self, message.action)
            if func.__code__.co_argcount == 1:  # the '1' is 'self'
                # function with no inputs
                reply = func()
            else:
                reply = func(**message.parameters)
            self.rabbit.send(RabbitMessageReply.create_reply(message, reply))
            logger.info(
                config.log_formatter(self, self.name, f"Action | {message.action}: {message.parameters}"))

        except Exception as e:
            logger.exception(config.log_formatter(self, self.name, "ActionError" + message.to_str()))
            self.rabbit.send(RabbitMessageError(self.name, f"ActionError: {message.to_str()}"))

    def _error_handling(self):
        """ Deactivate all equipment """
        for equip in self.registry.equipment:
            self.rabbit.send(RabbitMessageAction(equip, self.name, ""))
        self._deactivate()

    def read_equipment_status(self) -> EquipmentRegistry:
        """ read equipment status"""
        return self.registry

    def write_deactivate(self):
        pass
