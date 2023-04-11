import enum
import abc
import logging
import threading
import queue
import signal

from unitpy import Quantity

from chembot.configuration import config
from chembot.rabbitmq.message import RabbitMessage
from chembot.rabbitmq.core import RabbitCommunication

logger = logging.getLogger(config.root_logger_name + ".equipment")


class EquipmentState(enum.Enum):
    OFFLINE = 0
    PREACTIVATION = 1
    STANDBY = 2
    SCHEDULED_FOR_USE = 3
    TRANSIENT = 4
    RUNNING = 5
    SHUTTING_DOWN = 6
    CLEANING = 7
    ERROR = 8


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
        self.rabbit = RabbitCommunication(name)
        self.actions = self._get_actions_list()
        self._deactivate_event = threading.Event()
        self._reply_callback = None
        self.equipment_config = EquipmentConfig()

    def _get_actions_list(self) -> list[str]:
        actions = []
        for func in dir(self):
            if callable(getattr(self, func)) and (func.startswith("action_") or func.startswith("set_")):
                actions.append(func)

        return actions

    def activate(self):
        logger.debug(config.log_formatter(type(self).__name__, self.name, "Activating"))
        self.rabbit.activate()
        self._activate()
        logger.info(config.log_formatter(type(self).__name__, self.name, "Activated"))
        self.equipment_config.state = self.equipment_config.states.STANDBY

        try:
            self._run()
        except KeyboardInterrupt:
            logger.info(config.log_formatter(type(self).__name__, self.name, "KeyboardInterrupt"))
        finally:
            self._deactivate_()
            logger.info(config.log_formatter(type(self).__name__, self.name, "Deactivated"))

    def _run(self):
        # infinite loop
        while not self._deactivate_event.wait(timeout=1):
            try:
                message = self.rabbit.queue.get(block=False)
            except queue.Empty:
                continue

            if message.action == "reply":
                self._disarm_reply_alarm(message)

            if message.action in self.actions:
                try:
                    func = getattr(self, message.action)
                    func(message)
                except Exception as e:
                    logger.exception(
                        config.log_formatter(type(self).__name__, self.name, "ActionError" + message.to_str())
                    )
                    self.rabbit.send_error("ActionError", message.to_str())
            else:
                logger.warning("Invalid message action!!" + message.to_str())
                self.rabbit.send_error("InvalidMessage", message.to_str())

    def action_status(self, _: RabbitMessage = None):
        message = RabbitMessage("status", self.name, "update", self.state.name)
        self.rabbit.send(message)

    def action_help(self, _: RabbitMessage = None):
        message = RabbitMessage("help", self.name, "help", self.__doc__)
        self.rabbit.send(message)

    def action_actions(self, _: RabbitMessage = None):
        message = RabbitMessage("actions", self.name, "actions", self.actions)
        self.rabbit.send(message)

    def action_details(self, _: RabbitMessage = None):
        message = RabbitMessage("details", self.name, "actions", self._get_details())
        self.rabbit.send(message)

    def action_deactivate(self, _: RabbitMessage = None):
        self._deactivate_event.set()
        # self._deactivate is called by self._run

    def _deactivate_(self):
        logger.debug(config.log_formatter(type(self).__name__, self.name, "Deactivating"))
        self.equipment_config.state = self.equipment_config.states.SHUTTING_DOWN
        self.rabbit.deactivate()

    def _set_reply_alarm(self, time: int, callback=None):
        self._reply_callback = callback
        self._signal = signal.signal(signal.SIGALRM, self._raise_reply_alarm)
        signal.alarm(time)

    def _raise_reply_alarm(self):
        logger.error(config.log_formatter(type(self).__name__, self.name, "Reply alarm not disarmed"))
        self.rabbit.send_error("NoReply", "")

    def _disarm_reply_alarm(self, message):
        signal.alarm(0)  # disarms alarm
        self._reply_callback(message)
        self._reply_callback = None

    @abc.abstractmethod
    def _get_details(self) -> dict:
        ...

    @abc.abstractmethod
    def _activate(self) -> dict:
        ...

    @abc.abstractmethod
    def _deactivate(self):
        ...
