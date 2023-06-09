from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable, Iterator, Sequence

from chembot.scheduler.event import Event, EventResource, EventCallable, EventNoOp
from chembot.scheduler.job import Job
from chembot.scheduler.resource import Resource


def loop_through_jobs(schedule: Schedule, obj: Job | Event):
    """ depth-first-traverse through job graph """
    if isinstance(obj, Event):
        if isinstance(obj, EventCallable):
            schedule.add_event(obj.callable_.__name__, obj)
        elif isinstance(obj, EventResource):
            schedule.add_event(obj.resource, obj)
        elif isinstance(obj, EventNoOp):
            schedule.add_event(obj.name, obj)
    elif isinstance(obj, Job):
        for obj_ in obj.events:
            loop_through_jobs(schedule, obj_)
    else:
        raise ValueError("Not valid event.")


class Schedule:
    delay = timedelta(seconds=15)  # delay if no jobs are in queue

    def __init__(self, time_now: Callable[[], datetime] = None):
        self._resources: list[Resource] = []
        self._resources_labels = []
        self._job_running = None
        self._jobs_completed = []
        self._jobs_in_queue = []
        self._time_now = time_now if time_now is not None else datetime.now
        self._time_min = None
        self._time_max = None
        self._up_to_date = False

    def __iter__(self):
        return iter(self._resources)

    @property
    def time_now(self) -> datetime:
        return self._time_now()

    @property
    def resources(self) -> list[Resource]:
        return self._resources

    @property
    def jobs(self) -> list[Job]:
        return self.jobs_in_queue + [self.job_running] + self.jobs_completed

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
    def number_of_resources(self) -> int:
        return len(self._resources)

    @property
    def resources_labels(self) -> list[str]:
        if not self._up_to_date:
            self._update()
        return self._resources_labels

    @property
    def time_min(self) -> datetime | None:
        if not self._up_to_date:
            self._update()
        return self._time_min

    @property
    def time_max(self) -> datetime | None:
        if not self._up_to_date:
            self._update()
        return self._time_max

    @property
    def time_range(self) -> timedelta | None:
        if self.time_max is None or self.time_min is None:
            return None

        return self.time_max - self.time_min

    def _update(self):
        if self._resources:
            self._time_min, self._time_max = get_min_max_time(self.resources)

        self._resources_labels = [resources.name for resources in self.resources]
        self._up_to_date = True

    def get_resources(self, name: str) -> Resource:
        index = self.resources_labels.index(name)
        return self._resources[index]

    def add_resource(self, resource: Resource | Iterator[Resource]):
        self._up_to_date = False
        if isinstance(resource, Resource):
            resource = [resource]
        self._resources += resource

    def get_job(self, job: str) -> Job:
        pass

    def add_job(self, job: Job):
        self._jobs_in_queue.append(job)
        # determine job time

        loop_through_jobs(self, job)
        self._up_to_date = False

    def get_event(self, event: str | int) -> Event:
        pass

    def add_event(self, resource: str | Resource, event: Event):
        if isinstance(resource, str):
            if resource in self.resources_labels:
                resource = self.get_resources(resource)
            else:
                resource = Resource(resource)
                self.add_resource(resource)
        elif isinstance(resource, Resource):
            if resource in self.resources:
                pass
            else:
                self.add_resource(resource)
        else:
            raise ValueError("Invalid 'resource' value")

        resource.add_event(event)

    # def delete_job(self, job: Job | Iterator[Job]):
    #     self._up_to_date = False
    #
    #     if isinstance(row, int):
    #         del self._rows[row]
    #     elif isinstance(row, Row):
    #         self._rows.remove(row)
    #     elif isinstance(row, Iterator):
    #         for row_ in row:
    #             self._rows.remove(row_)
    #     else:
    #         raise ValueError("Invalid argument provided.")
    #
    # def delete_event(self, event: Event, Iterator[Event]):
    #     pass


def get_min_max_time(resources: Sequence[Resource]) -> tuple[datetime | None, datetime | None]:
    min_time = resources[0].time_start
    max_time = min_time
    for event in resources:
        if event.time_start < min_time:
            min_time = event.time_start
            continue
        if event.time_end is not None and event.time_end > max_time:
            max_time = event.time_end

    return min_time, max_time


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
