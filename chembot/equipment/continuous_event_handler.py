import abc
import typing
from typing import Callable, Sequence
import time
import logging

from chembot.configuration import config
from chembot.rabbitmq.messages import RabbitMessage, RabbitMessageAction
from chembot.utils.buffers.buffer_ring import BufferRingTimeSavable

logger = logging.getLogger(config.root_logger_name + ".continuous_event_handler")


class ParentInterfaceContinuousEventHandler(typing.Protocol):
    name: str

    def _execute_action(self, message: RabbitMessage, func_name: str, kwargs: dict | None):
        ...


class ContinuousEventHandler(abc.ABC):
    def __init__(self, callable_: str | Callable):
        self.callable_ = callable_ if isinstance(callable_, str) else callable_.__name__
        self.message: RabbitMessageAction | None = None

        self._start_time = None
        self._next_time = None
        self.event_counter: int = 0

    def __str__(self):
        return f"{type(self).__name__}.{self.callable_.__name__}"

    def __repr__(self):
        return self.__str__()

    @property
    def next_time(self) -> float | None:
        return self._next_time

    @property
    def start_time(self) -> float | None:
        return self._start_time

    @start_time.setter
    def start_time(self, start_time: float):
        if start_time < time.time():
            raise ValueError("Start time can't be earlier than current time.")

        self._start_time = start_time

    def poll(self, parent: ParentInterfaceContinuousEventHandler):
        """ function called each cycle of the equipment to run the profile. """
        try:
            if self._next_time > time.time():
                return
        except TypeError:  # self._next_time = None
            if self.start_time is None:
                logger.warning(f"Start time not set on '{parent.name} profile'.")
            parent.profile = None
            return

        self._set_next_time()

        # execute call
        self.event_counter += 1
        return parent._execute_action(self.message, self.callable_, self._get_kwargs())

    @abc.abstractmethod
    def _get_kwargs(self) -> dict:
        ...

    @abc.abstractmethod
    def _set_next_time(self):
        ...


class ContinuousEventHandlerRepeatingNoEnd(ContinuousEventHandler):
    def __init__(self,
                 callable_: str | Callable,
                 kwargs: dict[str, ...] = None,
                 delay_between_measurements: float | int = 0,  # in seconds
                 ):
        super().__init__(callable_)

        self.kwargs = kwargs
        self.delay_between_measurements = delay_between_measurements

    def __str__(self):
        if self.kwargs is not None:
            text = f"({''.join([str(k)+'='+str(v) for k, v in self.kwargs.items()])})"
        else:
            text = "()"
        return super().__str__() + text

    def _get_kwargs(self) -> dict:
        return self.kwargs

    def _set_next_time(self):
        return time.time() + self.delay_between_measurements


class ContinuousEventHandlerRepeating(ContinuousEventHandlerRepeatingNoEnd):
    def __init__(self,
                 callable_: str | Callable,
                 kwargs: dict[str, ...],
                 max_repeats: int,
                 delay_between_measurements: float | int = 0,  # in seconds
                 ):
        super().__init__(callable_, kwargs, delay_between_measurements)
        self.max_repeats = max_repeats

    def poll(self, parent: ParentInterfaceContinuousEventHandler):
        super().poll(parent)
        if self.max_repeats is not None and self.max_repeats == self.event_counter:
            parent.profile = None


class ContinuousEventHandlerProfile(ContinuousEventHandler):
    def __init__(self,
                 callable_: str | Callable,
                 kwargs_names: Sequence[str, ...],
                 kwargs_values: Sequence,
                 delay_between_measurements: Sequence[float | int],
                 ):
        super().__init__(callable_)
        self.kwargs_names = kwargs_names

        if len(kwargs_values) != len(delay_between_measurements):
            raise ValueError("len(kwargs_values) must equal len(time_delta_values).\n"
                             f"\tlen(kwargs_values): {len(kwargs_values)}"
                             f"\tlen(kwargs_values): {len(delay_between_measurements)}"
                             )
        self.kwargs_values = kwargs_values
        self.delay_between_measurements = delay_between_measurements
        self._times = None

    def _get_kwargs(self) -> dict:
        return {k: v for k, v in zip(self.kwargs_names, self.kwargs_values[self.event_counter])}

    def _set_next_time(self):
        return self._times[self.event_counter]


class ContinuousEventHandlerRepeatingConditional(ContinuousEventHandlerRepeating):
    def __init__(self,
                 callable_: str | Callable,
                 kwargs: dict[str, ...],
                 max_repeats: int,
                 condition: Callable,
                 delay_between_measurements: float | int = 0,  # in seconds
                 ):
        super().__init__(callable_, kwargs, delay_between_measurements)
        self.max_repeats = max_repeats

    def poll(self, parent: ParentInterfaceContinuousEventHandler):
        super().poll(parent)
        if self.max_repeats is not None and self.max_repeats == self.event_counter:
            parent.profile = None


class ContinuousEventHandlerRepeatingNoEndSaving(ContinuousEventHandlerRepeatingNoEnd):
    def __init__(self,
                 callable_: str | Callable,
                 kwargs: dict[str, ...] = None,
                 buffer_type: type = BufferRingTimeSavable,
                 delay_between_measurements: float | int = 0,  # in seconds
                 ):
        super().__init__(callable_, kwargs, delay_between_measurements)
        self._buffer_type = buffer_type
        self.buffer = None

    def poll(self, parent: ParentInterfaceContinuousEventHandler):
        result = super().poll(parent)
        if self.buffer is None:
            # we delay creating the buffer till the continuous event handler is on the equipment to avoid pass
            # large numpy arrays over rabbitmq
            self.buffer = self._buffer_type()
        self.buffer.add_data(result)
        return result
