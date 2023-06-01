import abc
import uuid

from chembot.scheduler.triggers import Trigger


class Event(abc.ABC):
    def __init__(self,
                 trigger: Trigger,
                 args: list | tuple = None,
                 kwargs: dict[str, object] = None,
                 id_: int | str = None,
                 priority: int = 0
                 ):
        self.id_ = id_ if id_ is not None else uuid.uuid4().int
        self.trigger = trigger
        self.priority = priority
        self.args = args
        self.kwargs = kwargs

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
                 args: list | tuple = None,
                 kwargs: dict[str, object] = None,
                 id_: int | str = None,
                 priority: int = 0
                 ):
        super().__init__(trigger=trigger, args=args, kwargs=kwargs, id_=id_, priority=priority)
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
                 args: list | tuple = None,
                 kwargs: dict[str, object] = None,
                 id_: int | str = None,
                 priority: int = 0
                 ):
        super().__init__(trigger=trigger, args=args, kwargs=kwargs, id_=id_, priority=priority)
        self.resource = resource
        self.callable_ = callable_

    def __str__(self):
        return f"{type(self).__name__} | {self.resource}.{self.callable_}({self.args},{self.kwargs})" \
               f" | trigger: {self.trigger}"

    def _run(self):
        pass
