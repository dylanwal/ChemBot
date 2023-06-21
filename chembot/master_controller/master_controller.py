import logging
from datetime import datetime, timedelta

from chembot.configuration import config
from chembot.equipment.equipment import Equipment
from chembot.utils.class_building import get_actions_list
from chembot.rabbitmq.messages import RabbitMessage, RabbitMessageAction, RabbitMessageCritical, RabbitMessageError, \
    RabbitMessageRegister, RabbitMessageReply, RabbitMessageUnRegister
from chembot.rabbitmq.rabbit_core import RabbitMQConnection
from chembot.rabbitmq.watchdog import RabbitWatchdog
from chembot.equipment.equipment_interface import EquipmentRegistry
from chembot.scheduler.schedule import Schedule
from chembot.scheduler.schedular import Schedular
from chembot.scheduler.submit_result import JobSubmitResult
from chembot.scheduler.validate import validate_schedule
from chembot.scheduler.job import Job

logger = logging.getLogger(config.root_logger_name + ".master_controller")


class MasterController:
    """ Master Controller """
    name = "master_controller"
    pulse = 0.01  # time of each loop in seconds
    status_update_time = timedelta(seconds=1)  # update all equipment status every 1 seconds

    def __init__(self):
        self.actions = get_actions_list(self)
        self.rabbit = RabbitMQConnection(self.name)
        self.watchdog = RabbitWatchdog(self)
        self.registry = EquipmentRegistry()
        self.scheduler = Schedular()
        self._deactivate_event = True  # False to deactivate
        self._next_update = datetime.now()

    def _deactivate(self):
        for equip in self.registry.equipment:
            self.rabbit.send(RabbitMessageAction(equip, self.name, Equipment.write_deactivate))
        self.rabbit.deactivate()
        logger.info(config.log_formatter(self, self.name, "Deactivated"))
        self._deactivate_event = False

    def activate(self):
        logger.info(config.log_formatter(self, self.name, "Activated\n" + "#" * 80 + "\n\n"))
        error_ = None
        try:
            self._run()
        except Exception as e:
            logger.critical(str(e))
            error_ = e

        except KeyboardInterrupt:
            logger.info(config.log_formatter(self, self.name, "KeyboardInterrupt"))

        finally:
            self._deactivate()

        if error_ is not None:
            raise error_

    def _run(self):
        # infinite loop
        while self._deactivate_event:
            self.watchdog.check_watchdogs()
            self._read_message()  # blocking with timeout
            self._run_event()
            self._status_update()

    def _run_event(self):
        event = self.scheduler.get_event_to_run()
        if event is None:
            return

        self.rabbit.send(
            RabbitMessageAction(
                destination=event.resource,
                source=self.name,
                action=event.callable_,
                kwargs=event.kwargs
            )
        )

    def _read_message(self):
        message = self.rabbit.consume(self.pulse)
        if message:
            self._process_message(message)

    def _process_message(self, message: RabbitMessage):
        if isinstance(message, RabbitMessageCritical):
            self._error_handling()
            self._deactivate_event = False
        elif isinstance(message, RabbitMessageError):
            self._error_handling()
            self._deactivate_event = False
        elif isinstance(message, RabbitMessageRegister):
            self.registry.register(message.source, message.equipment_interface)
            self.rabbit.send(RabbitMessageReply.create_reply(message, None))
        elif isinstance(message, RabbitMessageUnRegister):
            self.registry.unregister(message.source)
        elif isinstance(message, RabbitMessageAction):
            self._execute_action(message)
        elif isinstance(message, RabbitMessageReply):
            self.watchdog.deactivate_watchdog(message)
        else:
            logger.error("Invalid message!!" + message.to_str())
            self.rabbit.send(RabbitMessageError(self.name, f"InvalidMessage: {message.to_str()}"))

    def _execute_action(self, message):
        if message.action not in self.actions:
            logger.error("Invalid action!!" + message.to_str())
            self.rabbit.send(RabbitMessageError(self.name, f"Invalid action: {message.to_str()}"))

        try:
            func = getattr(self, message.action)
            if func.__code__.co_argcount == 1:  # the '1' is 'self'
                reply = func()
            else:
                reply = func(**message.kwargs)

            if reply is not None:
                self.rabbit.send(RabbitMessageReply.create_reply(message, reply))

            logger.info(
                config.log_formatter(self, self.name, f"Action | {message.action}: {message.kwargs}"))

        except Exception as e:
            logger.error(config.log_formatter(self, self.name, "ActionError" + message.to_str()))
            logger.error(e)
            logger.info("master controller continues to operate as nothing happened.")

    def _error_handling(self):
        """ Deactivate all equipment """
        self._deactivate()

    def _status_update(self):
        if datetime.now() > self._next_update:
            return

        self._next_update = datetime.now() + self.status_update_time

        # for equipment in self.registry.equipment:
        #     message = RabbitMessageUpdate(equipment.name)
        #     self.rabbit.send(message)
        #     self.watchdog.set_watchdog(message, delay=1)

    def read_equipment_registry(self) -> EquipmentRegistry:
        """ read equipment status"""
        return self.registry

    def read_schedule(self) -> Schedular:
        return self.scheduler

    def write_add_job(self, job: Job) -> JobSubmitResult:
        result = JobSubmitResult(job.id_)
        job.time_start = datetime.now()  # add temporarily
        schedule = Schedule.from_job(job)

        # validate schedule
        validate_schedule(schedule, self.registry, result)
        if not result.validation_success:
            return result

        # find next best time in schedule
        self.scheduler.add_job(job)
        result.time_start = self.scheduler.jobs_in_queue[-1].time_start
        result.position_in_queue = len(self.scheduler.jobs_in_queue)
        result.length_of_queue = len(self.scheduler.jobs_in_queue)
        result.success = True

        return result

    def write_stop(self):
        self.scheduler.clear_all_jobs()
        for equip in self.registry.equipment:
            self.rabbit.send(RabbitMessageAction(equip, self.name, Equipment.write_stop))

    def write_forward_reply(self, message: RabbitMessageReply, destination: str):
        message.destination = destination
        self.rabbit.send(message)

    def write_deactivate(self):
        pass
