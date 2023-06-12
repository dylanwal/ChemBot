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

        while True:
            pass

# def get_min_max_time(resources: Sequence[Resource]) -> tuple[datetime | None, datetime | None]:
#     min_time = resources[0].time_start
#     max_time = min_time
#     for event in resources:
#         if event.time_start < min_time:
#             min_time = event.time_start
#             continue
#         if event.time_end is not None and event.time_end > max_time:
#             max_time = event.time_end
#
#     return min_time, max_time


def get_time_delta_label(time_delta: timedelta) -> str:
    if time_delta >= timedelta(days=1):
        return f"{time_delta.days} d"
    if time_delta >= timedelta(hours=1):
        return f"{int(time_delta.seconds / 60 / 60)} h"
    if time_delta >= timedelta(minutes=1):
        return f"{int(time_delta.seconds / 60)} min"
    if time_delta >= timedelta(seconds=1):
        return f"{time_delta.seconds} s"
    return f"{time_delta.microseconds} ms"