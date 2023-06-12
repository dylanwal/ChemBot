from __future__ import annotations

from typing import Collection
import uuid

from chembot.scheduler.triggers import Trigger, TriggerSignal, TriggerNow
from chembot.scheduler.event import Event


class Job:
    def __init__(self,
                 events: Collection[Event | Job, ...] = None,
                 trigger: Trigger = None,
                 name: str = None,
                 completion_signal: str | TriggerSignal = None,
                 ):
        self.id_ = uuid.uuid4().int
        self.name = name

        self._events = []
        if events is not None:
            self.add_event(events)

        self.trigger: Trigger = trigger if trigger is not None else TriggerNow()

        if isinstance(completion_signal, TriggerSignal):
            completion_signal = completion_signal.signal
        self.completion_signal = completion_signal

        self.parent = None
        self.completed = False
        self.time_start = None
        self.time_end = None

    def __str__(self):
        text = ""
        if self.name is not None:
            text += self.name + " | "
        text += f"# events: {len(self)} | "
        if self.trigger is not None:
            text += f"{self.trigger}"
        text += f" | completed: {self.completed}"
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
    def events(self) -> list[Event | Job, ...]:
        return self._events

    def add_event(self, event: Collection[Event | Job, ...] | Event | Job):
        if isinstance(event, Job) or isinstance(event, Event):
            event = [event]

        self._events += event
        for event_ in event:
            event_.parent = self
