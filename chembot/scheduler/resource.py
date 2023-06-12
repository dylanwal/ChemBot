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
        self._events: list[Event] = []

    def __str__(self):
        return f"{self.name} | # events: {len(self._events)}"

    def __repr__(self):
        return self.__str__()

    @property
    def events(self) -> list[Event]:
        return self._events

    def add_event(self, event: Event):
        self._events.append(event)

    def validate_event(self, event: Event):
        pass
