from __future__ import annotations

import abc
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
                 args: list | tuple = None,
                 kwargs: dict[str, object] = None,
                 priority: int = 0,
                 name: str = None,
                 parent: Parent = None
                 ):
        if name is None:
            name = f"{resource}.{callable_}"
        self.name = name
        if isinstance(callable_, Callable):
            callable_ = callable_.__name__
        self.resource = resource
        self.callable_ = callable_
        self.duration = duration
        self.priority = priority
        self.args = args
        self.kwargs = kwargs
        self.delay = delay
        self.parent = parent

        self.id_ = uuid.uuid4().int
        self.completed = False
        self.time_start_actual = None
        self.time_start_actual = None

    def __str__(self):
        text = f"{self.resource}.{self.callable_}("
        if self.args is not None:
            text += ", ".join(self.args)
        if self.kwargs is not None:
            text += ",".join(f"{k}: {v}" for k, v in self.kwargs.items())
        text += ")"
        return text + f" | {self.duration}"

    def __repr__(self):
        return self.__str__()

    def __call__(self, *args, **kwargs):
        func = self._call()
        if self.args and self.kwargs is None:
            return func(*self.args)
        elif self.kwargs and self.args is None:
            return func(**self.kwargs)
        elif self.args and self.kwargs:
            return func(*self.args, **self.kwargs)
        return func()

    @property
    def time_start(self) -> datetime:
        if self.delay is not None:
            return self.parent._get_time_start(self) + self.delay

        return self.parent._get_time_start(self)

    @property
    def time_end(self) -> datetime:
        return self.time_start + self.duration

    @abc.abstractmethod
    def _call(self) -> callable:
        ...

    def hover_text(self) -> str:
        return f"duration: {self.duration}<br>" \
               f"job: {self.parent.root.name}<br>" \
               f"action: {self.callable_}"
