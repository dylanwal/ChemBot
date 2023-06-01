from __future__ import annotations

from typing import Collection
import uuid

from chembot.scheduler.triggers import Trigger, TriggerNow
from chembot.scheduler.event import Event


class Job:
    def __init__(self, events: Collection[Event | Job], trigger: Trigger = None, name: str = None):
        self.events = events
        self.trigger = trigger if trigger is None else TriggerNow()
        self.id_ = uuid.uuid4().int
        self.name = name if name is not None else str(self.id_)

    def __str__(self):
        return f"{type(self).__name__} | # events: {len(self)} | trigger: {self.trigger}"

    def __len__(self):
        return len(self.events)
