import time
from datetime import datetime, timedelta

from chembot.scheduler.job import Job
from chembot.scheduler.schedule import Schedule


class JobSubmitResult:

    def __init__(self,
                 success: bool = None,
                 time_start: datetime = None,
                 position_in_queue: int = None,
                 length_of_queue: int = None,
                 errors: list[Exception] = None
                 ):
        self.success = success
        self.time_start = time_start
        self.position_in_queue = position_in_queue
        self.length_of_queue = length_of_queue
        self.errors = errors if errors is not None else []

    def register_error(self, error: Exception):
        self.success = False
        self.errors.append(error)


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

    def add_job(self, job: Job) -> JobSubmitResult:
        # validate equipment, actions
        # validate no overlapping events
        # determine available time
        # add
        # return result
        ...
