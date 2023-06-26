from __future__ import annotations

import uuid
from typing import Iterator

from chembot.scheduler.event import Event
from chembot.scheduler.job import Job
from chembot.scheduler.resource import Resource


def loop_through_jobs(schedule: Schedule, obj: Job | Event):
    """ depth-first-traverse through job graph """
    if isinstance(obj, Event):
        schedule.add_event(obj.resource, obj)
    elif isinstance(obj, Job):
        for obj_ in obj.events:
            loop_through_jobs(schedule, obj_)
    else:
        raise ValueError("Not valid event.")


class Schedule:

    def __init__(self, id_: int = None):
        self.id_ = id_ if id_ is not None else uuid.uuid4().int
        self._resources: list[Resource] = []
        self._resources_labels = []
        self._jobs = []

    def __str__(self):
        return f"jobs: {len(self._jobs)} | resources: {len(self._resources)}"

    def __iter__(self):
        return iter(self._resources)

    @property
    def resources(self) -> list[Resource]:
        return self._resources

    @property
    def jobs(self) -> list[Job]:
        return self._jobs

    @property
    def number_of_resources(self) -> int:
        return len(self._resources)

    @property
    def resources_labels(self) -> list[str]:
        return [resources.name for resources in self.resources]

    def get_resources(self, name: str) -> Resource:
        index = self.resources_labels.index(name)
        return self._resources[index]

    def add_resource(self, resource: Resource | Iterator[Resource]):
        if isinstance(resource, Resource):
            resource = [resource]
        self._resources += resource

    def get_job(self, job: str) -> Job:
        pass

    def add_job(self, job: Job):
        self._jobs.append(job)
        # determine job time

        loop_through_jobs(self, job)

    def get_event(self, event: str | int) -> Event:
        raise NotImplementedError

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

    @classmethod
    def from_job(cls, job: Job) -> Schedule:
        schedule = cls(job.id_)
        schedule.add_job(job)
        return schedule
