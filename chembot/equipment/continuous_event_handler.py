import abc
import typing
from typing import Callable
from datetime import datetime, timedelta
import copy

from chembot.rabbitmq.rabbit_core import RabbitMQConnection
from chembot.rabbitmq.messages import RabbitMessageAction, RabbitMessageReply


def linspace_datetime(start: datetime, end: datetime, n: int) -> list[datetime]:
    time_span = (end - start).total_seconds()
    interval = time_span / n
    return [start + i * timedelta(seconds=interval) for i in range(n)]


def linspace_timedelta(start: timedelta, end: timedelta, n: int) -> list[timedelta]:
    time_span = (end - start).total_seconds()
    interval = time_span / n
    return [start + i * timedelta(seconds=interval) for i in range(n)]


class ParentInterface(typing.Protocol):
    rabbit: RabbitMQConnection


class ContinuousEventHandler(abc.ABC):
    def __init__(self,
                 callable_: str | Callable,
                 ):
        self.callable_ = callable_ if isinstance(callable_, str) else callable_.__name__
        self._start_time = None
        self.message: RabbitMessageAction | None = None
        self._event_counter: int = 0

    def __str__(self):
        return self.callable_

    def __repr__(self):
        return self.__str__()

    @abc.abstractmethod
    def __next__(self):
        ...

    @property
    def start_time(self) -> datetime | None:
        return self._start_time

    @start_time.setter
    def start_time(self, start_time: datetime):
        if start_time < datetime.now():
            raise ValueError("Start time can't be earlier than current time.")

        self._start_time = start_time

    @staticmethod
    def linspace_datetime(start: datetime, end: datetime, n: int) -> list[datetime]:
        return linspace_datetime(start, end, n)

    @staticmethod
    def linspace_timedelta(start: timedelta, end: timedelta, n: int) -> list[timedelta]:
        return linspace_timedelta(start, end, n)

    def poll(self, parent: ParentInterface):
        """ function called each cycle of the equipment to run the profile. """
        try:
            time_, kwargs = next(self)
            if time_ > datetime.now():
                self._event_counter -= 1
                return

        except StopIteration:
            parent.profile = None
            return

        func = getattr(parent, self.callable_)
        if func.__code__.co_argcount == 1:  # the '1' is 'self'
            reply = func()
        else:
            reply = func(**kwargs)

        if reply is not None:
            parent.rabbit.send(RabbitMessageReply.create_reply(self.message, reply))


class ContinuousEventHandlerRepeating(ContinuousEventHandler):
    def __init__(self,
                 callable_: str | Callable,
                 kwargs: dict[str, ...]
                 ):
        super().__init__(callable_)
        self.kwargs = kwargs

        def __str__():
            pass

        def __next__(self):
            ...



class ContinuousEventHandlerProfile(ContinuousEventHandler):
        def __init__(self,
                     callable_: str | Callable,
                     kwargs_name: list[str, ...],
                     kwargs_values: list,
                     time_delta_values: list[timedelta],
                     name: str = None
                     ):
            self.callable_ = callable_ if isinstance(callable_, str) else callable_.__name__
            self.kwargs_name = kwargs_name

            if len(kwargs_values) != len(time_delta_values):
                raise ValueError("len(kwargs_values) must equal len(time_delta_values).\n"
                                 f"\tlen(kwargs_values): {len(kwargs_values)}"
                                 f"\tlen(kwargs_values): {len(time_delta_values)}"
                                 )
            self.kwargs_values = kwargs_values
            self.time_delta_values = time_delta_values
            self._start_time = None
            self._name = name
            self.message: RabbitMessageAction | None = None
            self._next_counter: int = 0

        def __str__(self):
            return self.name

        def __repr__(self):
            return self.__str__()

        def __next__(self):
            try:
                result = (
                    self.start_time + self.time_delta_values[self._next_counter],
                    self.step_as_dict(self._next_counter, with_time=False)
                )
            except IndexError:
                self._next_counter = 0
                raise StopIteration
            self._next_counter += 1
            return result

        @property
        def name(self) -> str:
            if self._name is None:
                return f"{self.callable_}({','.join(self.kwargs_name)})"

            return self._name

        @name.setter
        def name(self, name: str):
            self._name = name

        @property
        def number_of_steps(self) -> int:
            return len(self.kwargs_values)

        @property
        def duration(self) -> timedelta:
            return self.time_delta_values[-1]

        @property
        def start_time(self) -> datetime | None:
            return self._start_time

        @start_time.setter
        def start_time(self, start_time: datetime):
            if start_time < datetime.now():
                raise ValueError("Start time can't be earlier than current time.")

            self._start_time = start_time

        @property
        def time_values(self) -> list[datetime]:
            self._start_time = datetime.now()
            return [self.start_time + time_delta for time_delta in self.time_delta_values]

        def step_as_dict(self, i: int = 0, with_time: bool = True) -> dict:
            keys = copy.copy(self.kwargs_name)
            values = [copy.copy(self.kwargs_values[i])]
            if with_time:
                keys.append("time_delta")
                values.append(self.time_delta_values[i])
            return {k: v for k, v in zip(keys, values)}

        @staticmethod
        def linspace_datetime(start: datetime, end: datetime, n: int) -> list[datetime]:
            return linspace_datetime(start, end, n)

        @staticmethod
        def linspace_timedelta(start: timedelta, end: timedelta, n: int) -> list[timedelta]:
            return linspace_timedelta(start, end, n)

        def poll(self, parent):
            """ function called each cycle of the equipment to run the profile. """
            try:
                time_, kwargs = next(self)
                if time_ > datetime.now():
                    self._next_counter -= 1
                    return

            except StopIteration:
                parent.profile = None
                return

            func = getattr(parent, self.callable_)
            if func.__code__.co_argcount == 1:  # the '1' is 'self'
                reply = func()
            else:
                reply = func(**kwargs)

            if reply is not None:
                parent.rabbit.send(RabbitMessageReply.create_reply(self.profile.message, reply))

