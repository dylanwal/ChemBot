from __future__ import annotations

import uuid
from typing import Protocol, Callable
from datetime import datetime, timedelta


class Parent(Protocol):
    """ Protocol which mirrors Job """
    time_start: datetime
    name: str
    root: Parent

    def _get_time_start(self, obj) -> datetime:
        ...


class Event:
    def __init__(self,
                 resource: str,
                 callable_: str | Callable,
                 duration: timedelta,
                 *,
                 delay: timedelta = None,
                 kwargs: dict[str, object] = None,
                 priority: int = 0,
                 name: str = None,
                 parent: Parent = None
                 ):
        if isinstance(callable_, Callable):
            callable_ = callable_.__name__
        if name is None:
            name = f"{resource}.{callable_}"
        self.name = name
        self.resource = resource
        self.callable_ = callable_
        self._duration = duration
        self.priority = priority
        self.kwargs = kwargs
        self.delay = delay
        self.parent = parent

        self.id_ = uuid.uuid4().int
        self.completed = False

    def __str__(self):
        text = f"{self.resource}.{self.callable_}("
        if self.kwargs is not None:
            text += ",".join(f"{k}: {v}" for k, v in self.kwargs.items())
        text += ")"
        return text + f" | {self.duration}"

    def __repr__(self):
        return self.__str__()

    @property
    def time_start(self) -> datetime:
        """ includes delay """
        return self.parent._get_time_start(self)

    @property
    def time_start_actual(self) -> datetime:
        """ does not include delay """
        time_ = self.time_start
        if self.delay is not None:
            time_ += self.delay
        return time_

    @property
    def time_end(self) -> datetime:
        return self.time_start + self._duration

    @property
    def root(self) -> Parent:
        return self.parent.root

    @property
    def duration(self) -> timedelta:
        """ includes delay """
        return self.time_end - self.time_start

    @property
    def duration_actual(self) -> timedelta:
        """ does not include delay """
        return self.time_end - self.time_start_actual

    def hover_text(self) -> str:
        return f"duration: {self.duration}<br>" \
               f"job: {self.parent.root.name}<br>" \
               f"action: {self.callable_}"
