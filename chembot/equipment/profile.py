from typing import Callable, Sequence
from datetime import datetime, timedelta


def linspace_datetime(start: datetime, end: datetime, n: int) -> list[datetime]:
    time_span = (end - start).total_seconds()
    interval = time_span / n
    return [start + i * timedelta(seconds=interval) for i in range(n)]


def linspace_timedelta(start: timedelta, end: timedelta, n: int) -> list[timedelta]:
    time_span = (end - start).total_seconds()
    interval = time_span / n
    return [start + i * timedelta(seconds=interval) for i in range(n)]


class Profile:

    def __init__(self,
                 callable_: str | Callable,
                 kwargs_name: Sequence[str, ...],
                 kwargs_values: Sequence,
                 time_delta_values: Sequence[timedelta],
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

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

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

    @staticmethod
    def linspace_datetime(start: datetime, end: datetime, n: int) -> list[datetime]:
        return linspace_datetime(start, end, n)

    @staticmethod
    def linspace_timedelta(start: timedelta, end: timedelta, n: int) -> list[timedelta]:
        return linspace_timedelta(start, end, n)
