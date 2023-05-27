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


def get_attrs(class_) -> set:
    results = set()
    for func in dir(class_):
        if callable(getattr(class_, func)) and func.startswith("read_"):
            attr = func.strip("read_")
            if hasattr(class_, attr):
                results.add(attr)

    return results


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
        self.rabbit = RabbitMQConnection(name)
        self.actions = get_actions_list(self)
        self.attrs = get_attrs(self)
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

        # update parameters
        self.equipment_interface.parameters = self.read_all()

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
            logger.debug(config.log_formatter(self, self.name, "Deactivating"))
            self._deactivate()
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
                reply = func(**message.kwargs)
            self.rabbit.send(RabbitMessageReply.create_reply(message, reply))
            logger.info(
                config.log_formatter(self, self.name, f"Action | {message.action}: {message.kwargs}"))

        except Exception as e:
            logger.exception(config.log_formatter(self, self.name, "ActionError" + message.to_str()))
            self.rabbit.send(RabbitMessageError(self.name, f"ActionError: {message.to_str()}"))

    def read_all(self) -> dict:
        """
        returns values off all properties that can be 'read'

        Returns
        -------
        results:

        """
        return {attr: getattr(self, attr) for attr in self.attrs}

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
        self.equipment_config.state = self.equipment_config.states.SHUTTING_DOWN
        # TODO un-register
        self.rabbit.deactivate()

    @abc.abstractmethod
    def _activate(self):
        ...

    @abc.abstractmethod
    def _deactivate(self):
        ...
