import abc
import logging
import threading
import queue

from unitpy import Quantity

from chembot.configuration import config
from chembot.equipment.equipment_interface import EquipmentState, get_equipment_interface
from chembot.rabbitmq.messages import RabbitMessage, RabbitMessageState, RabbitMessageAction, RabbitMessageRegister
from chembot.rabbitmq.core import RabbitCommunication

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
    def __init__(self, name: str):
        self.name = name
        self.state: EquipmentState = EquipmentState.OFFLINE
        self.rabbit = RabbitCommunication(f"equipment.{name}")
        self.actions = self._get_actions_list()
        self._deactivate_event = threading.Event()
        self._reply_callback = None
        self.equipment_config = EquipmentConfig()
        self.equipment_interface = get_equipment_interface(self)

    def _get_actions_list(self) -> list[str]:
        actions = []
        for func in dir(self):
            if callable(getattr(self, func)) and (func.startswith("read_") or func.startswith("write_")):
                actions.append(func)

        return actions

    def activate(self):
        logger.debug(config.log_formatter(self, self.name, "Activating"))
        self.rabbit.activate()
        self._activate()
        self.read_register()
        logger.info(config.log_formatter(self, self.name, "Activated"))
        self.equipment_config.state = self.equipment_config.states.STANDBY

        try:
            self._run()
        except KeyboardInterrupt:
            logger.info(config.log_formatter(self, self.name, "KeyboardInterrupt"))
        finally:
            self._deactivate_()
            logger.info(config.log_formatter(self, self.name, "Deactivated"))

    def _run(self):
        # infinite loop
        while not self._deactivate_event.wait(timeout=0.1):
            try:
                message = self.rabbit.queue.get(block=False)
                self.process_message(message)
            except queue.Empty:
                continue

    def process_message(self, message: RabbitMessage):
        if isinstance(message, RabbitMessageAction) and message.action in self.actions:
            try:
                func = getattr(self, message.action)
                func(message)
            except Exception as e:
                logger.exception(
                    config.log_formatter(self, self.name, "ActionError" + message.to_str())
                )
                self.rabbit.send_error(f"ActionError: {message.to_str()}")
        else:
            logger.warning("Invalid message action!!" + message.to_str())
            self.rabbit.send_error(f"InvalidMessage: {message.to_str()}")

    def read_status(self, _: RabbitMessage = None):
        """ Get equipment status """
        message = RabbitMessageState(self.name, self.state.name)
        self.rabbit.send(message)

    def read_register(self, _: RabbitMessage = None):
        message = RabbitMessageRegister(self.equipment_interface)
        self.rabbit.send(message)

    def write_deactivate(self, _: RabbitMessage = None):
        self._deactivate_event.set()
        # self._deactivate is called by self._run

    def _deactivate_(self):
        logger.debug(config.log_formatter(type(self).__name__, self.name, "Deactivating"))
        self.equipment_config.state = self.equipment_config.states.SHUTTING_DOWN
        self.rabbit.deactivate()

    @abc.abstractmethod
    def _get_details(self) -> dict:
        ...

    @abc.abstractmethod
    def _activate(self) -> dict:
        ...

    @abc.abstractmethod
    def _deactivate(self):
        ...
