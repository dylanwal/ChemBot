from __future__ import annotations

from typing import Collection
import uuid
from datetime import datetime

from chembot.scheduler.triggers import Trigger, TriggerNow
from chembot.scheduler.event import Event


class Job:
    def __init__(self, events: Collection[Event | Job], trigger: Trigger = None, name: str = None):
        self.events = events
        self.trigger = trigger if trigger is not None else TriggerNow()
        self.id_ = uuid.uuid4().int
        self.name = name

        self._start_time = None

    @property
    def start_time(self) -> datetime | None:
        return self._start_time

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
