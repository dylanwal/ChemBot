from __future__ import annotations

from typing import Collection
import uuid
from datetime import datetime

from chembot.scheduler.triggers import Trigger, TriggerSignal
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

        self.trigger = trigger  # if None will be filled with TriggerNow()

        if isinstance(completion_signal, TriggerSignal):
            self.completion_signal = completion_signal.signal
        self.completion_signal = completion_signal

        self._start_time = None
        self.completed = False

    def __str__(self):
        text = ""
        if self.name is not None:
            text += self.name + " | "
        text += f"# events: {len(self)} | "
        return text + f"{self.trigger}"

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

    @property
    def start_time(self) -> datetime | None:
        return self._start_time

    def add_event(self, event: Collection[Event | Job, ...] | Event | Job):
        if isinstance(event, Job) or isinstance(event, Event):
            event = [event]

        self._events += event
