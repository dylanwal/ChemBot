import time

from chembot.scheduler.triggers import Trigger
from chembot.scheduler.event import Event
from chembot.scheduler.job import Job
from chembot.scheduler.resource import Resource


class Schedule:
    def __init__(self):
        self.jobs: list[Job] = []

    def submit_job(self, job: Job):
        pass


class Schedular:
    def __init__(self, timer: callable = None):
        self.timer = timer if timer is None else time.monotonic
        self.schedule = Schedule()
        self.resources: set[Resource] = set()

    def register_resources(self):
        pass


