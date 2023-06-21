from __future__ import annotations

import time
from datetime import timedelta, datetime

from chembot.scheduler.event import Event
from chembot.scheduler.job import Job
from chembot.scheduler.schedule import Schedule


class Schedular:
    delay = timedelta(seconds=15)  # delay if no jobs are in queue

    def __init__(self, timer: callable = None):
        self.timer = timer if timer is None else time.monotonic
        self.schedule = Schedule()
        self._job_running: Job | None = None
        self._jobs_completed: list[Job] = []
        self._jobs_in_queue: list[Job] = []

    @property
    def jobs_completed(self) -> list[Job]:
        return self._jobs_completed

    @property
    def job_running(self) -> Job | None:
        return self._job_running

    @property
    def jobs_in_queue(self) -> list[Job]:
        return self._jobs_in_queue

    @property
    def end_time(self) -> datetime | None:
        if self._jobs_in_queue:
            return self._jobs_in_queue[-1].time_end
        if self._job_running:
            return self._job_running.time_end
        return None

    def get_event_to_run(self) -> Event | None:
        now = datetime.now()
        for resource in self.schedule.resources:
            if now > resource.next_event.time_start:
                next_event = resource.next_event

                # update job lists
                if next_event.root is not self._job_running:
                    self._jobs_completed.append(self._job_running)
                    self._job_running = self._jobs_in_queue.pop(0)

                return next_event

    def add_job(self, job: Job):
        # determine available time
        # TODO: not robust to deletions or moving event/jobs; should pass reference
        time_start = self.get_possible_start_time_for_schedule()
        job.time_start = time_start

        # add to queue
        self._jobs_in_queue.append(job)
        self.schedule.add_job(job)

    def get_possible_start_time_for_schedule(self) -> datetime:
        return self.end_time + self.delay  # TODO could be improved.
