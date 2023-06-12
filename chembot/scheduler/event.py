import abc
import uuid
from datetime import datetime, timedelta

from chembot.scheduler.triggers import Trigger, TriggerSignal


class Event(abc.ABC):
    def __init__(self,
                 trigger: Trigger,
                 args: list | tuple = None,
                 kwargs: dict[str, object] = None,
                 priority: int = 0,
                 name: str = None,
                 completion_signal: TriggerSignal | str | int = None,
                 estimated_time: timedelta = None
                 ):
        self.id_ = uuid.uuid4().int
        self.name = name
        self.trigger = trigger
        self.priority = priority
        self.args = args
        self.kwargs = kwargs
        if isinstance(completion_signal, TriggerSignal):
            completion_signal = completion_signal.signal
        self.completion_signal = completion_signal
        self.estimated_time = estimated_time
        self.parent = None

        self.completed = False
        self.time_start = None
        self.time_end = None

    def __repr__(self):
        return self.__str__()

    # def __eq__(self, obj):
    #     return (self.time_start, self.priority) == (obj.time_, obj.priority)
    #
    # def __lt__(self, obj):
    #     return (self.time_start, self.priority) < (obj.time_, obj.priority)
    #
    # def __le__(self, obj):
    #     return (self.time_start, self.priority) <= (obj.time_, obj.priority)
    #
    # def __gt__(self, obj):
    #     return (self.time_start, self.priority) > (obj.time_, obj.priority)
    #
    # def __ge__(self, obj):
    #     return (self.time_start, self.priority) >= (obj.time_, obj.priority)

    def run(self):
        func = self._run()
        if self.args and self.kwargs is None:
            return func(*self.args)
        elif self.kwargs and self.args is None:
            return func(**self.kwargs)
        elif self.args and self.kwargs:
            return func(*self.args, **self.kwargs)
        return func()

    @abc.abstractmethod
    def _run(self) -> callable:
        ...


class EventCallable(Event):
    def __init__(self,
                 callable_: callable,
                 trigger: Trigger,
                 *,
                 args: list | tuple = None,
                 kwargs: dict[str, object] = None,
                 priority: int = 0,
                 name: str = None,
                 completion_signal: TriggerSignal | str | int = None,
                 estimated_time: timedelta = None
                 ):
        if name is None:
            name = callable_.__name__
        super().__init__(trigger=trigger, args=args, kwargs=kwargs, name=name, priority=priority,
                         completion_signal=completion_signal, estimated_time=estimated_time)
        self.callable_ = callable_

    def __str__(self):
        text = self.callable_.__name__ + "("
        if self.args is not None:
            text += ", ".join(self.args)
        if self.kwargs is not None:
            text += ",".join(f"{k}: {v}" for k, v in self.kwargs.items())
        text += ")"
        return text + f" | {self.trigger}"

    def _run(self) -> callable:
        return self.callable_


class EventResource(Event):
    def __init__(self,
                 resource: str,
                 callable_: str,
                 trigger: Trigger,
                 *,
                 args: list | tuple = None,
                 kwargs: dict[str, object] = None,
                 priority: int = 0,
                 name: str = None,
                 completion_signal: TriggerSignal | str | int = None,
                 estimated_time: timedelta = None
                 ):
        if name is None:
            name = f"{resource}.{callable_}"
        super().__init__(trigger=trigger, args=args, kwargs=kwargs, name=name, priority=priority,
                         completion_signal=completion_signal, estimated_time=estimated_time)
        self.resource = resource
        self.callable_ = callable_

    def __str__(self):
        text = f"{self.resource}.{self.callable_}("
        if self.args is not None:
            text += ", ".join(self.args)
        if self.kwargs is not None:
            text += ",".join(f"{k}: {v}" for k, v in self.kwargs.items())
        text += ")"
        return text + f" | {self.trigger}"

    def _run(self):
        pass


class EventNoOp(Event):
    name: str = "no_op"

    def __init__(self,
                 trigger: Trigger,
                 *,
                 priority: int = 0,
                 completion_signal: TriggerSignal | str | int = None,
                 estimated_time: timedelta = None
                 ):
        super().__init__(trigger=trigger, name=self.name, priority=priority,
                         completion_signal=completion_signal, estimated_time=estimated_time)

    def __str__(self):
        return f"No op | {self.trigger}"

    def _run(self):
        pass
