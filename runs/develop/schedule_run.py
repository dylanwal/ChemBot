
from chembot.scheduler.triggers import TriggerTimeAbsolute, TriggerTimeRelative, TriggerSignal
from chembot.scheduler.event import EventCallable, EventResource
from chembot.scheduler.job import Job
from chembot.scheduler.resource import Resource, ResourceGroup
from chembot.scheduler.base import Schedular

scheduler = Schedular()


def func1():
    print("l")


job = Job([
    EventCallable()
])

scheduler.schedule.submit_job()


