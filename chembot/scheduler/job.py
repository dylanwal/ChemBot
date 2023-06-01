from __future__ import annotations

from typing import Collection
import uuid

from chembot.scheduler.triggers import Trigger, TriggerNow
from chembot.scheduler.event import Event


class Job:
    def __init__(self, events: Collection[Event | Job], trigger: Trigger = None, id_: int | str = None):
        self.events = events
        self.trigger = trigger if trigger is None else TriggerNow()
        self.id_ = id_ if id_ is not None else uuid.uuid4().int

    def __str__(self):
        return f"{type(self).__name__} | # events: {len(self)} | trigger: {self.trigger}"

    def __len__(self):
        return len(self.events)
