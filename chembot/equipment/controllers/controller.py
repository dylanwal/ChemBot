from typing import Callable

from chembot.configuration import config
from chembot.utils.class_building import get_actions_list
from chembot.equipment.equipment_interface import EquipmentState, get_equipment_interface
from chembot.rabbitmq.messages import RabbitMessage, RabbitMessageReply, RabbitMessageAction, RabbitMessageRegister, \
    RabbitMessageError, RabbitMessageCritical, RabbitMessageUnRegister
from chembot.rabbitmq.rabbit_core import RabbitMQConnection
from chembot.rabbitmq.watchdog import RabbitWatchdog


class Controller:

    def __init__(self, name: str, func: Callable):
        self.rabbit = RabbitMQConnection(name)
        self.watchdog = RabbitWatchdog(self)
        self.func = func

    def activate(self):
        """ Called to start equipment infinite loop. """
        try:
            logger.debug(config.log_formatter(self, self.name, "Activating"))
            self._activate()
            self._register_equipment()
            logger.info(config.log_formatter(self, self.name, "Activated\n" + "#" * 80 + "\n\n"))
            self.state = self.states.STANDBY

            self._run()  # infinite loop

        except KeyboardInterrupt:
            logger.info(config.log_formatter(self, self.name, "KeyboardInterrupt"))

        finally:
            logger.debug(config.log_formatter(self, self.name, "Deactivating"))

            try:
                self._deactivate()
                self._deactivate_()
            except Exception as e:
                logger.exception(str(e))
            logger.info(config.log_formatter(self, self.name, "Deactivated"))
