from typing import Collection
import abc
import time
import datetime


class Trigger(abc.ABC):

    @property
    @abc.abstractmethod
    def triggered(self) -> bool:
        ...


class TriggerNow(Trigger):
    def __init__(self):
        pass

    def triggered(self) -> bool:
        return True


class TriggerTimeRelative(Trigger):
    """ also called interval """

    def __init__(self, trigger_time: int | float | datetime.datetime):
        self.trigger_time = trigger_time  # TODO: convert datetime
        self._start_time = None

    def __str__(self):
        return f"{type(self).__name__} | trigger_time: {self.trigger_time}"

    def triggered(self) -> bool:
        return self.trigger_time + self._start_time > time.time()


class TriggerTimeAbsolute(Trigger):
    def __init__(self, trigger_time: int | float | datetime.datetime):
        self.trigger_time = trigger_time  # TODO: convert datetime

    def __str__(self):
        return f"{type(self).__name__} | trigger_time: {self.trigger_time}"

    def triggered(self) -> bool:
        return self.trigger_time > time.time()


class TriggerSignal(Trigger):
    def __init__(self, signal: int | float | str):
        self.signal = signal
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
    def __init__(self, triggers: Collection[Trigger], *args):
        self.triggers = triggers

    def __str__(self):
        return f"{type(self).__name__} | number_triggers: {len(self)}"

    def __len__(self):
        return len(self.triggers)

    def triggered(self) -> bool:
        return all(trigger.triggered for trigger in self.triggers)