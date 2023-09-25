from __future__ import annotations

import time
from datetime import timedelta, datetime
import logging

from chembot.configuration import config
from chembot.scheduler.event import Event
from chembot.scheduler.job import Job
from chembot.scheduler.schedule import Schedule


logger = logging.getLogger(config.root_logger_name + ".schedular")


class Schedular:
    delay = timedelta(seconds=2)  # delay if no jobs are in queue

    def __init__(self, timer: callable = None):
        self.timer = timer if timer is None else time.monotonic
        self.schedule = Schedule()
        self._job_running: Job | None = None
        self._jobs_completed: list[Job] = []
        self._jobs_in_queue: list[Job] = []

    def __str__(self):
        return "Schedular:" \
               f"\n\tRunning: {self._job_running}" \
               f"\n\tCompleted: {self._jobs_completed}" \
               f"\n\tIn queue (# jobs: {len(self._jobs_in_queue)}):  {self._jobs_in_queue}"

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
    def time_end(self) -> datetime | None:
        if self._jobs_in_queue:
            return self._jobs_in_queue[-1].time_end
        if self._job_running:
            return self._job_running.time_end

        return None

    def get_event_to_run(self) -> Event | None:
        now = datetime.now()
        for resource in self.schedule.resources:
            if resource.next_event is None:
                continue

            if now > resource.next_event.time_start_with_delay:
                next_event = resource.next_event
                self._update_job_lists(next_event.root)
                resource.next_event_index += 1
                return next_event

    def _update_job_lists(self, job):
        if job is not self._job_running:
            if self._job_running is not None:
                self._jobs_completed.append(self._job_running)
            self._job_running = self._jobs_in_queue.pop(0)

    def add_job(self, job: Job):
        # determine available time
        # TODO: not robust to deletions or moving event/jobs; should pass reference
        time_start = self.get_possible_start_time_for_schedule()
        job.time_start = time_start

        # add to queue
        self._jobs_in_queue.append(job)
        self.schedule.add_job(job)

    def get_possible_start_time_for_schedule(self) -> datetime:
        end_time = self.time_end
        if end_time is None or end_time < datetime.now():
            end_time = datetime.now()

        return end_time + self.delay  # TODO: could be improved.

    def clear_all_jobs(self):
        self._job_running = None
        self._jobs_in_queue = []
        self.schedule = Schedule()
