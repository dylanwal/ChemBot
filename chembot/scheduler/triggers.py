import uuid
from typing import Collection
import abc
import time
from datetime import datetime, timedelta


class Trigger(abc.ABC):

    @property
    @abc.abstractmethod
    def triggered(self) -> bool:
        ...


class TriggerNow(Trigger):
    def __init__(self):
        pass

    def __str__(self):
        return type(self).__name__

    def triggered(self) -> bool:
        return True


class TriggerTimeRelative(Trigger):
    """ also called interval """

    def __init__(self, trigger_time: timedelta):
        self.trigger_time = trigger_time
        self._start_time = None

    def __str__(self):
        return f"{type(self).__name__} | trigger_time: {self.trigger_time}"

    def triggered(self) -> bool:
        return self.trigger_time + self._start_time > time.time()


class TriggerTimeAbsolute(Trigger):
    def __init__(self, trigger_time: datetime):
        self.trigger_time = trigger_time

    def __str__(self):
        return f"{type(self).__name__} | trigger_time: {self.trigger_time}"

    def triggered(self) -> bool:
        return self.trigger_time > datetime.now()


class TriggerSignal(Trigger):
    def __init__(self, signal: int | float | str = None):
        self.signal = signal if signal is not None else uuid.uuid4()
        self._signaled = False

    def __str__(self):
        return f"{type(self).__name__} | signal: {self.signal}"

    def triggered(self) -> bool:
        return self._signaled

    def set_signal(self, signal: int | float | str) -> bool:
        if signal == self.signal:
            self._signaled = True
            return True
        return False


class TriggerCombine(Trigger, abc.ABC):
    ...


class TriggerOr(TriggerCombine):
    def __init__(self, triggers: Collection[Trigger]):
        self.triggers = triggers

    def __str__(self):
        return f"{type(self).__name__} | number_triggers: {len(self)}"

    def __len__(self):
        return len(self.triggers)

    def triggered(self) -> bool:
        return any(trigger.triggered for trigger in self.triggers)


class TriggerAnd(TriggerCombine):
    def __init__(self, triggers: Collection[Trigger]):
        self.triggers = triggers

    def __str__(self):
        return f"{type(self).__name__} | number_triggers: {len(self)}"

    def __len__(self):
        return len(self.triggers)

    def triggered(self) -> bool:
        return all(trigger.triggered for trigger in self.triggers)
