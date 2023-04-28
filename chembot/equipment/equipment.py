import abc
import logging
import threading

from unitpy import Quantity

from chembot.configuration import config
from chembot.equipment.equipment_interface import EquipmentState, get_equipment_interface
from chembot.rabbitmq.messages import RabbitMessage, RabbitMessageReply, RabbitMessageAction, RabbitMessageRegister, \
    RabbitMessageError, RabbitMessageCritical
from chembot.rabbitmq.core import RabbitMQConnection

logger = logging.getLogger(config.root_logger_name + ".equipment")


def get_actions_list(class_) -> list[str]:
    actions = []
    for func in dir(class_):
        if callable(getattr(class_, func)) and (func.startswith("read_") or func.startswith("write_")):
            actions.append(func)

    return actions


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
    def __init__(self, name: str, **kwargs):
        self.name = name
        self.state: EquipmentState = EquipmentState.OFFLINE
        self.rabbit = RabbitMQConnection(f"equipment.{name}")
        self.actions = get_actions_list(self)
        self._deactivate_event = threading.Event()
        self._reply_callback = None
        self.equipment_config = EquipmentConfig()
        self.equipment_interface = get_equipment_interface(self)

        if kwargs:
            for k, v in kwargs:
                setattr(self, k, v)

    def _register_equipment(self, _: RabbitMessage = None):
        if not self.rabbit.queue_exists("master_controller"):
            logger.info(config.log_formatter(self, self.name, "No MasterController found on the server."))
            raise ValueError()

        self.rabbit.send(RabbitMessageRegister(self.name, self.equipment_interface))

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
        while not self._deactivate_event.wait(timeout=0.1):
            message = self.rabbit.consume()
            if message is None:
                continue

            self.process_message(message)

    def process_message(self, message: RabbitMessage):
        if isinstance(message, RabbitMessageCritical):
            self._deactivate_event.set()

        elif isinstance(message, RabbitMessageError):
            self._deactivate_event.set()

        elif isinstance(message, RabbitMessageAction) and message.action in self.actions:
            try:
                func = getattr(self, f"_{message.action}_message")
                func(message)
            except Exception as e:
                logger.exception(config.log_formatter(self, self.name, "ActionError" + message.to_str()))
                self.rabbit.send(RabbitMessageError(self.name, f"ActionError: {message.to_str()}"))
        else:
            logger.warning("Invalid message action!!" + message.to_str())
            self.rabbit.send(RabbitMessageError(self.name, f"InvalidMessage: {message.to_str()}"))

    def _read_all_message(self, message: RabbitMessageAction):
        self.rabbit.send(RabbitMessageReply(message, self.read_all()))

    def read_all(self) -> dict:
        """
        read_all
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

    def _read_state_message(self, message: RabbitMessageAction):
        self.rabbit.send(RabbitMessageReply(message, self.read_state()))

    def read_state(self) -> EquipmentState:
        """
        read_state
        Get equipment status

        Returns
        -------
        state:
            current state of equipment

        """
        return self.state

    def _read_name_message(self, message: RabbitMessageAction):
        self.rabbit.send(RabbitMessageReply(message, self.read_name()))

    def read_name(self) -> str:
        """ read_name """
        return self.name

    def _write_name_message(self, message: RabbitMessageAction):
        self.write_name(message.value)
        self.rabbit.send(RabbitMessageReply(message, ""))

    def write_name(self, name: str):
        """ write_name """
        self.name = name

    def _write_deactivate_message(self, message: RabbitMessageAction):
        self.write_deactivate()
        self.rabbit.send(RabbitMessageReply(message, ""))

    def write_deactivate(self):
        """
        write_deactivate
        deactivate equipment (shut down)

        """
        self._deactivate_event.set()
        # self._deactivate is called by self._run

    def _deactivate_(self):
        logger.debug(config.log_formatter(type(self).__name__, self.name, "Deactivating"))
        self.equipment_config.state = self.equipment_config.states.SHUTTING_DOWN
        self.rabbit.deactivate()

    @abc.abstractmethod
    def _activate(self):
        ...

    @abc.abstractmethod
    def _deactivate(self):
        ...
