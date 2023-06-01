import abc
import uuid

from chembot.scheduler.triggers import Trigger


class Event(abc.ABC):
    def __init__(self,
                 trigger: Trigger,
                 args: list | tuple = None,
                 kwargs: dict[str, object] = None,
                 priority: int = 0,
                 name: str = None,
                 completion_signal: str | int = None,
                 ):
        self.id_ = uuid.uuid4().int
        self.name = name if name is None else str(self.id_)
        self.trigger = trigger
        self.priority = priority
        self.args = args
        self.kwargs = kwargs
        self.completion_signal = completion_signal

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
                 completion_signal: str | int = None
                 ):
        super().__init__(trigger=trigger, args=args, kwargs=kwargs, name=name, priority=priority,
                         completion_signal=completion_signal)
        self.callable_ = callable_

    def __str__(self):
        return f"{type(self).__name__} | {self.callable_.__name__}({self.args},{self.kwargs}) | trigger: {self.trigger}"

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
                 completion_signal: str | int = None
                 ):
        super().__init__(trigger=trigger, args=args, kwargs=kwargs, name=name, priority=priority,
                         completion_signal=completion_signal)
        self.resource = resource
        self.callable_ = callable_

    def __str__(self):
        return f"{type(self).__name__} | {self.resource}.{self.callable_}({self.args},{self.kwargs})" \
               f" | trigger: {self.trigger}"

    def _run(self):
        pass
