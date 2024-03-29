from __future__ import annotations

import abc
from datetime import timedelta, datetime
from typing import Collection
import uuid

from chembot.scheduler.event import Event


class Job(abc.ABC):
    def __init__(self,
                 events: Collection[Event | Job, ...] = None,
                 delay: timedelta = None,
                 name: str = None,
                 parent: Job = None,
                 time_start: datetime = None
                 ):
        self.id_ = uuid.uuid4().int
        self.name = name
        self.delay = delay
        self._ids: set[int] = set()
        self._events: list[Event] = []
        if events is not None:
            self.add_event(events)

        self.parent = parent
        self.completed = False
        self._time_start = time_start

    def __str__(self):
        text = type(self).__name__
        if self.name is not None:
            text += "|" + self.name
        text += f"(# events: {len(self)})"
        text += "completed" if self.completed else "not completed"
        return text

    def __repr__(self):
        return self.__str__()

    def __len__(self) -> int:
        count = 0
        for ev in self.events:
            if isinstance(ev, Job):
                count += len(ev)
            else:
                count += 1

        return count

    @property
    def id_job(self) -> int:
        if self.parent is not None:
            return self.parent.id_job
        return self.id_

    @property
    def time_start_with_delay(self) -> datetime:
        """ start time + job delay"""
        time_ = self.time_start
        if self.delay is not None:
            time_ += self.delay

        return time_

    @property
    def time_start(self) -> datetime | None:
        """ no job delay include in time """
        if self.parent is not None:
            return self.parent._get_time_start(self)
        if self._time_start is not None:
            return self._time_start

    @time_start.setter
    def time_start(self, time_start: datetime):
        if self.parent is not None:
            raise ValueError("Start time can not be set if there is a parent")

        self._time_start = time_start

    @property
    @abc.abstractmethod
    def duration(self) -> timedelta:
        ...

    @property
    def time_end(self) -> datetime | None:
        if self.time_start is None:
            return None
        return self.time_start + self.duration

    @property
    def events(self) -> list[Event | Job, ...]:
        return self._events

    @property
    def root(self) -> Job:
        if self.parent is None:
            return self
        return self.parent.root

    def add_event(self, event: Collection[Event | Job, ...] | Event | Job):
        if isinstance(event, Job) or isinstance(event, Event):
            event = [event]

        self._id_check(event)
        self._events += event
        for event_ in event:
            event_.parent = self

    def _id_check(self, events: Collection[Event | Job, ...]):
        for event in events:
            if event.id_ in self._ids:
                raise ValueError(
                    "Duplicate event not allowed. Events must be re-made from scratch to be performed twice.\n"
                    f"Duplicate event:{event.name} (id: {event.id_})"
                )
            self._ids.add(event.id_)

            if isinstance(event, Job):
                if len(self._ids.intersection(event._ids)) != 0:
                    raise ValueError(
                        "Duplicate event not allowed. Events must be re-made from scratch to be performed twice.\n"
                        f"Duplicate event:{event.name} (id: {event.id_})"
                    )
                self._ids = self._ids.union(event._ids)

    @abc.abstractmethod
    def _get_time_start(self, obj) -> datetime:
        ...


class JobSequence(Job):
    @property
    def duration(self) -> timedelta:
        sum_ = timedelta(0)
        for event_ in self.events:
            if event_.delay:
                event_duration = event_.duration + event_.delay
            else:
                event_duration = event_.duration
            sum_ += event_duration

        return sum_

    def _get_time_start(self, obj) -> datetime:
        index = self.events.index(obj)
        if index == 0:
            return self.time_start_with_delay

        return self.events[index-1].time_end


class JobConcurrent(Job):
    @property
    def duration(self) -> timedelta:
        max_ = timedelta(0)
        for event_ in self.events:
            if event_.delay:
                event_duration = event_.duration + event_.delay
            else:
                event_duration = event_.duration

            if max_ < event_duration:
                max_ = event_duration
        return max_

    def _get_time_start(self, obj) -> datetime:
        return self.time_start_with_delay
