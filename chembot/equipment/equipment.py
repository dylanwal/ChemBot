import abc
import logging
import queue
import time

from unitpy import Quantity

from chembot.configuration import config
from chembot.utils.class_building import get_actions_list
from chembot.equipment.equipment_interface import EquipmentState, get_equipment_interface
from chembot.rabbitmq.messages import RabbitMessage, RabbitMessageReply, RabbitMessageAction, RabbitMessageRegister, \
    RabbitMessageError, RabbitMessageCritical, RabbitMessageUnRegister
from chembot.rabbitmq.rabbit_core import RabbitMQConnection
from chembot.rabbitmq.watchdog import RabbitWatchdog
from chembot.equipment.continuous_event_handler import ContinuousEventHandler

logger = logging.getLogger(config.root_logger_name + ".equipment")


class EquipmentConfig:
    def __init__(self,
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
    pulse = 0.01  # time of each loop in seconds
    states = EquipmentState

    def __init__(self, name: str, **kwargs):
        """

        Parameters
        ----------
        name:
            class_name is a **unique** identifier in the system
        """
        # self._reply_callback = None
        # self.action_in_progress = None

        self.name = name
        self.state: EquipmentState = EquipmentState.OFFLINE
        self.actions = get_actions_list(self)
        self.equipment_interface = get_equipment_interface(type(self))
        self.attrs = []
        self.update = ["state"]

        # managers
        self.rabbit = RabbitMQConnection(name)
        self.watchdog = RabbitWatchdog(self)
        self.continuous_event_handler: ContinuousEventHandler | None = None
        self._message_queue = queue.Queue(maxsize=6)  # short term storage for later processing (typically used in
        # continuous mode)

        # flags
        self._deactivation_event = False  # set to True to deactivate

        if kwargs:
            for k, v in kwargs:
                setattr(self, k, v)

    def _register_equipment(self):
        if not self.rabbit.queue_exists("master_controller"):
            logger.critical(config.log_formatter(self, self.name, "No MasterController found on the server."))
            raise ValueError("No MasterController found on the server.")

        # update parameters
        message = RabbitMessageRegister(self.name, self.equipment_interface)
        self.rabbit.send_and_consume(message, error_out=True)

    def _unregister_equipment(self):
        if not self.rabbit.queue_exists("master_controller"):
            logger.critical(config.log_formatter(self, self.name, "No MasterController found, so can't skip "
                                                                  "unregistering."))
            return

        # update parameters
        message = RabbitMessageUnRegister(self.name)
        self.rabbit.send(message)
        self.watchdog.set_watchdog(message, 5)

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

    def _run(self):
        """ Main / infinite event loop """
        while not self._deactivation_event:
            self._poll_status()
            self.watchdog.check_watchdogs()

            # read message
            self._process_message(self.rabbit.consume())

            # execute continuous commands
            if self.continuous_event_handler is not None:
                self.continuous_event_handler.poll(self)
            else:
                time.sleep(self.pulse)

    def _poll_status(self):
        pass

    def _process_message(self, message: RabbitMessage):
        if message is None:
            return

        if isinstance(message, RabbitMessageCritical):
            self._deactivation_event = True
        elif isinstance(message, RabbitMessageError):
            self._deactivation_event = True
        elif isinstance(message, RabbitMessageReply):
            if message.id_reply in self.watchdog:
                self.watchdog.deactivate_watchdog(message)
            if message.queue_it:
                try:
                    self._message_queue.put(message, timeout=1)
                except queue.Full:
                    logger.exception('Build of RabbitMessageReply in queue. '
                                     f'The following message dropped: \n{message.to_str()}')
        elif isinstance(message, RabbitMessageAction):
            reply = self._execute_action(message, message.action, message.kwargs)
            if reply is not None:
                self.rabbit.send(RabbitMessageReply.create_reply(message, reply))
            logger.info(
                config.log_formatter(self, self.name, f"Action | {message.action}: {message.kwargs}"
                                                      f"\n reply: {repr(reply)}"))
        else:
            logger.warning("Invalid message!!" + message.to_str())
            self.rabbit.send(RabbitMessageError(self.name, f"InvalidMessage: {message.to_str()}"))

    def _execute_action(self, message: RabbitMessage, func_name: str, kwargs: dict | None):
        # TODO: wrap this into a thread and use a queue
        try:
            func = getattr(self, func_name)
            if func.__code__.co_argcount == 1 or kwargs is None:  # the '1' is 'self'
                reply = func()
            else:
                reply = func(**kwargs)

            # we need the message to be added to continuous_event_handler but not sure where best to put it
            if isinstance(message, RabbitMessageAction) and \
                    message.action == self.write_continuous_event_handler.__name__:
                self.continuous_event_handler.message = message

            return reply

        except Exception as e:
            logger.exception(config.log_formatter(self, self.name, "ActionError" + message.to_str()))
            self.rabbit.send(RabbitMessageError(self.name, f"ActionError: {message.to_str()}"), check=False)

    def read_all_attributes(self) -> dict:
        """
        returns attributes of the equipment

        Returns
        -------
        results:

        """
        return {attr: getattr(self, attr) for attr in self.attrs}

    def read_update(self) -> dict:
        """
        returns attributes of the equipment

        Returns
        -------
        results:

        """
        return {attr: getattr(self, attr) for attr in self.update}  # TODO: add sensors a

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
        returns equipment class_name
        """
        return self.name

    def write_name(self, name: str):
        """
        write a new class_name for the equipment
        """
        self.name = name

    def write_deactivate(self):
        """
        deactivate equipment (shut down)
        """
        self._stop()
        self._deactivation_event = True
        # self._deactivate is called by self._run

    def write_stop(self):
        """
        stop current action and reset to standby
        """
        self.state = EquipmentState.STANDBY
        if self.continuous_event_handler is not None:
            self.continuous_event_handler.stop()
            self.continuous_event_handler = None
        self._stop()

    def write_continuous_event_handler(self, event_handler: ContinuousEventHandler):
        """
        Set continuous_event_handler

        Parameters
        ----------
        event_handler

        """
        self.continuous_event_handler = event_handler
        self.continuous_event_handler.start_time = time.time()

    def _deactivate_(self):
        self.state = self.states.SHUTTING_DOWN
        self._unregister_equipment()
        self.rabbit.deactivate()

    @abc.abstractmethod
    def _activate(self):
        ...

    @abc.abstractmethod
    def _deactivate(self):
        ...

    @abc.abstractmethod
    def _stop(self):
        ...
