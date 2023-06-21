
from chembot.scheduler.event import Event


class Resource:
    """
    A resource is something which can processes event
    """
    def __init__(self, name: str):
        self.name = name
        self._events: list[Event] = []
        self.next_event_index: int = 0

    def __str__(self):
        return f"{self.name} | # events: {len(self._events)}"

    def __repr__(self):
        return self.__str__()

    @property
    def next_event(self) -> Event | None:
        if self.next_event_index == len(self._events):
            return None
        return self._events[self.next_event_index]

    @property
    def events(self) -> list[Event]:
        return self._events

    def add_event(self, event: Event):
        # insert events in temporal order by start at the end and loop forward.
        # most insertions should just be at the end.
        for i, event_ in enumerate(reversed(self._events)):
            if event.time_start > event_.time_start:
                if i == 0:
                    self._events.append(event)
                else:
                    self._events.insert(-i, event)
                return

        self._events.insert(0, event)

    def validate_event(self, event: Event):
        pass
