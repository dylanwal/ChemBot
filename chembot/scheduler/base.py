import sched
import time

from chembot.scheduler.event import Event
from chembot.rabbitmq.messages import RabbitMessageAction


class ScheduleParent:

    def write_event(self, message: RabbitMessageAction):
        ...


class Schedule(sched.scheduler):
    def __init__(self, parent: ScheduleParent):
        super().__init__(time.monotonic, time.sleep)
        self.parent = parent

    def add_event(self, event: Event):
        self.enter(event.time_, event.priority, self.parent.write_event, (event.message,))


