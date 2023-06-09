from typing import Collection
from datetime import timedelta
import bisect

from chembot.scheduler.event import Event


def insert_ordered_list(lst, obj, attribute):
    values = [getattr(item, attribute) for item in lst]
    index = bisect.bisect_left(values, getattr(obj, attribute))
    lst.insert(index, obj)


class Resource:
    """
    A resource is something which can processes event
    """
    def __init__(self, name: str):
        self.name = name
        self._events = []

    @property
    def events(self) -> list[Event]:
        return self._events

    def add_event(self, event: Event):
        # TODO: event validation with equipment interface
        self._events += event

    @property
    def time_start(self):
        pass

    @property
    def time_end(self):
        pass

    @property
    def time_till_next_event(self) -> timedelta | None:
        pass

    @property
    def next_event(self) -> Event | None:
        pass

def d():
    for time_block in row.time_blocks:
        if time_block.time_start < min_time:
            min_time = time_block.time_start
            continue
        if time_block.time_end is not None and time_block.time_end > max_time:
            max_time = time_block.time_end