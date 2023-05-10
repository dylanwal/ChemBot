import abc
import logging

from unitpy import Quantity

from chembot.configuration import config
from chembot.utils.class_building import get_actions_list
from chembot.equipment.equipment_interface import EquipmentState, get_equipment_interface
from chembot.rabbitmq.messages import RabbitMessage, RabbitMessageReply, RabbitMessageAction, RabbitMessageRegister, \
    RabbitMessageError, RabbitMessageCritical
from chembot.rabbitmq.rabbit_core import RabbitMQConnection
from chembot.rabbitmq.watchdog import RabbitWatchdog

logger = logging.getLogger(config.root_logger_name + ".equipment")


class EquipmentConfig:
    states = EquipmentState

    def __init__(self,
                 # sensors: list[Sensor],
                 max_pressure: Quantity = Quantity("1.1 atm"),
                 min_pressure: Quantity = Quantity("0.9 atm"),
                 max_temperature: Quantity = Quantity("15 degC"),
                 min_temperature: Quantity = Quantity("35 degC"),
                 ):
        self.max_pressure = max_pressure
        self.min_pressure = min_pressure
        self.max_temperature = max_temperature
        self.min_temperature = min_temperature


class Equipment(abc.ABC):
    """ Equipment """
    pulse = 0.1  # time of each loop in seconds

    def __init__(self, name: str, **kwargs):
        """

        Parameters
        ----------
        name:
            name is a **unique** identifier in the system
        """
        self.name = name
        self.state: EquipmentState = EquipmentState.OFFLINE
        self.rabbit = RabbitMQConnection(f"equipment.{name}")
        self.actions = get_actions_list(self)
        self._deactivate_event = False
        self._reply_callback = None
        self.equipment_config = EquipmentConfig()
        self.equipment_interface = get_equipment_interface(self)
        self.watchdog = RabbitWatchdog(self)

        if kwargs:
            for k, v in kwargs:
                setattr(self, k, v)

    def _register_equipment(self, _: RabbitMessage = None):
        if not self.rabbit.queue_exists("master_controller"):
            logger.info(config.log_formatter(self, self.name, "No MasterController found on the server."))
            raise ValueError("No MasterController found on the server.")

        message = RabbitMessageRegister(self.name, self.equipment_interface)
        self.rabbit.send(message)
        self.watchdog.set_watchdog(message, 5)

    def activate(self):
        try:
            logger.debug(config.log_formatter(self, self.name, "Activating"))
            self._activate()
            self._register_equipment()
            logger.info(config.log_formatter(self, self.name, "Activated"))
            self.equipment_config.state = self.equipment_config.states.STANDBY

            self._run()  # infinite loop

        except KeyboardInterrupt:
            logger.info(config.log_formatter(self, self.name, "KeyboardInterrupt"))
        finally:
            self._deactivate_()
            logger.info(config.log_formatter(self, self.name, "Deactivated"))

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
            self._deactivate_event = True

        elif isinstance(message, RabbitMessageError):
            self._deactivate_event = True

        elif isinstance(message, RabbitMessageAction) and message.action in self.actions:
            try:
                func = getattr(self, message.action)
                reply = func(message.parameters)
                self.rabbit.send(RabbitMessageReply(message, reply))
                logger.info(
                    config.log_formatter(self, self.name, f"Action | {message.action}: {message.parameters}"))
            except Exception as e:
                logger.exception(config.log_formatter(self, self.name, "ActionError" + message.to_str()))
                self.rabbit.send(RabbitMessageError(self.name, f"ActionError: {message.to_str()}"))

        elif isinstance(message, RabbitMessageReply):
            self.watchdog.deactivate_watchdog(message)

        else:
            logger.warning("Invalid message or action!!" + message.to_str())
            self.rabbit.send(RabbitMessageError(self.name, f"InvalidMessage: {message.to_str()}"))

    def read_all(self) -> dict:
        """
        returns values off all properties that can be 'read'

        Returns
        -------
        results:

        """
        results = {}
        for func in dir(self):
            if callable(getattr(self, func)) and func.startswith("read"):
                results[func] = getattr(self, func)()

        return results

    def read_state(self) -> EquipmentState:
        """
        Get equipment status

        Returns
        -------
        state:
            current state of equipment

        """
        return self.state

    def read_name(self) -> str:
        """
        returns equipment name
        """
        return self.name

    def write_name(self, name: str):
        """
        write a new name for the equipment
        """
        self.name = name

    def write_deactivate(self):
        """
        deactivate equipment (shut down)
        """
        self._deactivate_event = True
        # self._deactivate is called by self._run

    def _deactivate_(self):
        logger.info(config.log_formatter(self, self.name, "Deactivating"))
        self.equipment_config.state = self.equipment_config.states.SHUTTING_DOWN
        self.rabbit.deactivate()

    @abc.abstractmethod
    def _activate(self):
        ...

    @abc.abstractmethod
    def _deactivate(self):
        ...
