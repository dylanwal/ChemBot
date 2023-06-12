import time
from datetime import datetime, timedelta

from chembot.scheduler.job import Job
from chembot.scheduler.schedule import Schedule


class Schedular:
    delay = timedelta(seconds=15)  # delay if no jobs are in queue

    def __init__(self, timer: callable = None):
        self.timer = timer if timer is None else time.monotonic
        self.schedule = Schedule()
        self._job_running = None
        self._jobs_completed = []
        self._jobs_in_queue = []

    @property
    def jobs_completed(self) -> list[Job]:
        return self._jobs_completed

    @property
    def job_running(self) -> Job | None:
        return self._job_running

    @property
    def jobs_in_queue(self) -> list[Job]:
        return self._jobs_in_queue

    def run(self):
        # check if any events need to run
        # send messages out
        ...
