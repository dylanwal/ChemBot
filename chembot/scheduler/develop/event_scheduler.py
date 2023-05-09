"""
Designed using elements from sched.scheduler
"""

import enum
import heapq
import sys
import time
import threading

_sentinel = object()


def run_threaded(job_func: callable, args: dict | None, kwargs: dict | None):
    job_thread = threading.Thread(target=job_func, args=args, kwargs=kwargs)
    job_thread.start()


class Event:
    __slots__ = ("id_", "time_", "priority", "action", "args", "kwargs")

    def __init__(self, id_: int, time_, priority: int, action: callable, args: tuple, kwargs: dict):
        """
        
        Parameters
        ----------
        id_: int
            id of event
        time_: float
            Numeric type compatible with the return value of the timefunc function passed to the constructor.
        priority: int
        Events scheduled for the same time will be executed in the order of their priority.
        action: callable
            Executing the event means executing action(*argument, **kwargs)
        args: tuple
            argument is a sequence holding the positional arguments for the action.
        kwargs: dict
        kwargs is a dictionary holding the keyword arguments for the action.
        """
        self.id_ = id_
        self.time_ = time_
        self.priority = priority
        self.action = action
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        return str((self.id_, self.time_, self.priority, self.action, self.args, self.kwargs))

    def __eq__(self, obj): 
        return (self.time_, self.priority) == (obj.time_, obj.priority)

    def __lt__(self, obj): 
        return (self.time_, self.priority) < (obj.time_, obj.priority)

    def __le__(self, obj): 
        return (self.time_, self.priority) <= (obj.time_, obj.priority)

    def __gt__(self, obj): 
        return (self.time_, self.priority) > (obj.time_, obj.priority)

    def __ge__(self, obj): 
        return (self.time_, self.priority) >= (obj.time_, obj.priority)

    def __iter__(self):
        return iter((self.id_, self.time_, self.priority, self.action, self.args, self.kwargs))


class SchedulerStatus(enum.Enum):
    RUNNING = 0
    STOPPING = 1
    STOPPED = 2


class EventScheduler:
    """
    The Event Scheduler is an always-on scheduler which is able to accept and
    run events based on its scheduled time and priority.
    """

    def __init__(self,
                 timefunc=time.time,
                 timer_class=threading.Timer,
                 blocking: bool = False
                 ):
        """

        Parameters
        ----------
        timefunc
            provide a timing function the event scheduler will rely on to schedule events
        timer_class
            provide a timer class which runs on the same time as timefunc
        blocking: bool
            True: when events start, they stop the main flow
            False: events happen on isolated threads
        """
        self._queue = []
        self._lock = threading.RLock()
        self.timefunc = timefunc
        self._scheduler_status = SchedulerStatus.STOPPED
        self._event_thread = threading.Thread(target=self._run)
        # Condition variable to notify the event thread when there's a new
        # event or when the deadline of the soonest event has passed.
        self._cv = threading.Condition(self._lock)
        # If we've looked at the front of the queue and the event isn't ready
        # to execute, we set a timer for the remaining time. If a new event is
        # added to the queue, then we cancel the timer and set it to None.
        self._timer_class = timer_class
        self._timer = None
        # dictionary to store all currently active recurring events (key: id,
        # value: Event)
        self._recurring_events = {}
        # monotonically increasing counter to provide unique event_ids for
        # recurring events
        self._id_counter = 0
        self.blocking = blocking

    def empty(self) -> bool:
        """Check whether the queue is empty."""
        with self._lock:
            return not self._queue

    def _notify(self):
        with self._cv:
            self._cv.notify()

    def enterabs(self, time_: float, action: callable, args: tuple = (), kwargs=_sentinel, priority: int = 5) -> Event:
        """
        Enter a new event in the queue to occur at an absolute time.

        Parameters
        ----------
        time_: float
            The absolute time the event will be scheduled to execute.
        action: callable
            The function which will invoked when the event executes.
        args: tuple
            Variable length argument list for the action.
        kwargs: dict
            Keyword arguments for the action.
        priority: int
            The priority the event will execute with. If two events are scheduled for
            the same time, the event with the lower priority will execute first.

        Returns
        -------
        Event:
            The scheduled event if the scheduler is running, None
            otherwise. This can be used to cancel the event later, if
            necessary.

        Raises
        ------
        ValueError: If the 0 > priority >= sys.maxsize

        """
        if priority >= sys.maxsize or priority < 0:
            raise ValueError('Priority must be equal to or greater than 0 and less than sys.maxsize')

        if kwargs is _sentinel:
            kwargs = {}

        # Non-recurring events have an id of 0
        event = Event(0, time_, priority, action, args, kwargs)
        with self._lock:
            if self._scheduler_status != SchedulerStatus.RUNNING:
                return None
            heapq.heappush(self._queue, event)
            # We only want to notify the event thread if the inserted event is
            # in the front of the queue
            if event == self._queue[0]:
                self._notify()

        return event  # The ID

    def enter(self, delay: float, action: callable, args: tuple = (), kwargs: dict = _sentinel, priority: int = 5) \
            -> Event:
        """
        Enter a new event in the queue to occur at a time relative to the current time.

        Parameters
        ----------
        delay: float
            The relative time the event will be scheduled to execute.
            Eg. If you pass in 1 as the delay, the event will be scheduled
            to execute in 1 + now() seconds from now.
        action: callable
            The function which will invoked when the event executes.
        args: tuple
            Variable length argument list for the action.
        kwargs: dict
            Keyword arguments for the action.
        priority: int
            The priority the event will execute with. If two events are scheduled for
            the same time, the event with the lower priority will execute first.

        Returns
        -------
        Event:
            The scheduled event if the scheduler is running, None
            otherwise. This can be used to cancel the event later, if
            necessary.

        Raises
        ------
        ValueError: If the 0 > priority >= sys.maxsize

        """
        if priority >= sys.maxsize or priority < 0:
            raise ValueError('Priority must be equal to or greater than 0 and '
                             'less than sys.maxsize')
        time_ = self.timefunc() + delay
        return self.enterabs(time_, action, args, kwargs, priority)

    def enter_recurring(self,
                        interval,
                        priority,
                        action,
                        arguments=(),
                        kwargs=_sentinel) -> int:
        """Enter a new recurring event in the queue to occur at a specified
        interval.
        Args:
            interval: The interval time the event will be scheduled to execute.
                Eg. If you pass in 5 as the delay, the event will be scheduled to
                execute every 5 seconds starting five seconds from when it's
                entered.
            priority (int): The priority the event will execute with. If two
                events are scheduled for the same time, the event with the
                lower priority will execute first.
            action (callable): The function which will invoked when the event
                executes.
            arguments (optional): Variable length argument list for the action.
            kwargs (:obj:`dict`, optional): Keyword arguments for the action.
        Returns:
            int: An event id of the recurring event if the scheduler is
            running, None otherwise. This id can be used to cancel the event
            later, if necessary.
        Raises:
            ValueError: If the 0 > priority >= sys.maxsize
        Warning:
            Long running actions will stall the internal thread and may impact
            the scheduling of other events.
        """
        if priority >= sys.maxsize or priority < 0:
            raise ValueError('Priority must be equal to or greater than 0 and '
                             'less than sys.maxsize')
        if kwargs is _sentinel:
            kwargs = {}
        with self._lock:
            if self._scheduler_status != SchedulerStatus.RUNNING:
                return None
            self._id_counter += 1
            time_ = self.timefunc() + interval
            event = Event(self._id_counter,
                          time_,
                          priority,
                          action,
                          arguments,
                          kwargs
                          )
            self._recurring_events[self._id_counter] = (event, interval)
            heapq.heappush(self._queue, event)
            # We only want to notify the event thread if the inserted event is
            # in the front of the queue
            if event == self._queue[0]:
                self._notify()
            return self._id_counter

    def _reschedule_recurring(self, *args):
        """Logic to reschedule a recurring event. Only executed from the event
        scheduler thread while holding the queue lock.
        """
        time_, priority, action, argument, kwargs, event_id = args
        if event_id in self._recurring_events and \
                self._scheduler_status == SchedulerStatus.RUNNING:
            interval = self._recurring_events[event_id][1]
            # We do the scheduling based on the previous execution time
            event = Event(interval + time_,
                          priority,
                          action,
                          argument,
                          kwargs,
                          event_id)
            self._recurring_events[event_id] = (event, interval)
            heapq.heappush(self._queue, event)

    def cancel(self, event: Event) -> int:
        """Remove an event from the queue using the id returned by
        enter()/enterabs(). If the event is not in the queue, this is a no-op.
        Args:
            event: The event to be cancelled.
        Returns:
            int: 0 if the event was successfully removed/not in the queue, -1
            otherwise.
        """
        with self._lock:
            if self._scheduler_status != SchedulerStatus.RUNNING:
                return -1
            try:
                if self._queue and self._queue[0] == event:
                    self._notify()
                self._queue.remove(event)
                heapq.heapify(self._queue)
            except ValueError:
                pass
        return 0

    def cancel_recurring(self, event_id) -> int:
        """Remove recurring event from the queue using the id returned by
        enter_recurring(). If the recurring event is not in the queue, this is
        a no-op.
        Args:
            event_id (int): The id of the recurring event to be cancelled.
        Returns:
            int: 0 if the event was successfully removed/not in the queue, -1
            otherwise.
        """
        with self._lock:
            if self._scheduler_status != SchedulerStatus.RUNNING:
                return -1
            if event_id not in self._recurring_events:
                return 0
            event = self._recurring_events[event_id][0]
            del self._recurring_events[event_id]
            if self._queue and self._queue[0] == event:
                self._notify()
            self._queue.remove(event)
            heapq.heapify(self._queue)
            return 0

    def cancel_all(self) -> int:
        """Clear all events from the queue. If the queue is already empty, this
        is a no-op.
        Returns:
            int: 0 if all the events were successfully cleared, -1 otherwise.
        """
        with self._lock:
            if self._scheduler_status != SchedulerStatus.RUNNING:
                return -1
            if self._queue:
                self._queue.clear()
            if self._timer:
                self._timer.cancel()
                self._timer = None
            self._recurring_events.clear()
        return 0

    def _run(self):
        """ Execute events with the soonest time and lowest priority events
        executing first. If there aren't any events available to run, this
        thread uses a timer and waits on a condition variable. When the
        deadline for the event has passed, the timer calls notify() on the
        condition variable and the event action is executed.
        A terminating event is enqueued when the event scheduler is stopped
        and joins the event scheduler thread once the queue is drained.
        """
        # localize variable access to minimize overhead
        # and to improve thread safety
        cv = self._cv
        q = self._queue
        timer = self._timer
        timefunc = self.timefunc
        pop = heapq.heappop
        while True:
            with cv:
                if not q or timer:
                    cv.wait()
                if timer:
                    timer.cancel()
                    timer = None
                if not q:
                    continue
                event_id, time_, priority, action, args, kwargs,  = q[0]
                if priority == sys.maxsize:
                    pop(q)
                    self._notify()
                    break
                now = timefunc()
                if time_ > now:
                    # Event is not ready to execute. Initialize a timer to wake
                    # up this thread when the first event is ready to execute.
                    timer = self._timer_class(time_ - now, self._notify)
                    timer.start()
                    self._notify()
                    continue
                else:
                    # Take out the event from the queue since it's ready to
                    # execute
                    pop(q)
                if event_id:
                    self._reschedule_recurring(time_, priority, action,
                                               args, kwargs, event_id)

                # run event
                if self.blocking:
                    action(*args, **kwargs)
                else:
                    run_threaded(action, args, kwargs)

                self._notify()

    @property
    def queue(self) -> list:
        """Return an ordered list of upcoming events. Events are named tuples
        with fields for: time, priority, action, arguments, kwargs, id
        Returns:
            list: All the events currently in the queue ordered from the
            soonest to occur and by priority,
        """
        # Use heapq to sort the queue rather than using 'sorted(self._queue)'.
        # With heapq, two events scheduled at the same time will show in
        # the actual order they would be retrieved.
        with self._lock:
            events = self._queue[:]
            self._notify()
        return list(map(heapq.heappop, [events] * len(events)))

    def start(self) -> int:
        """Start the event scheduler and enable it to start taking events.
        Returns:
            int: 0 if the event scheduler was successfully started, -1 if the
            scheduler has already been started or is in the process of
            stopping.
        """
        with self._lock:
            if self._scheduler_status != SchedulerStatus.STOPPED:
                return -1
            self._event_thread.start()
            self._scheduler_status = SchedulerStatus.RUNNING
        return 0

    def stop(self, hard_stop: bool = False) -> int:
        """Stop the event scheduler and stop its internal thread. Will not be
        able to take in new events when invoked.
        Args:
            hard_stop (bool, optional): If set to `False`, wait until all
                events execute at their scheduled time before stopping. If set
                to `True`, will stop the scheduler right away and discard all
                pending events.
        Returns:
            int: 0 if the event scheduler was successfully stopped, -1 if the
            scheduler is already in the process of stopping/already stopped.
        """
        with self._lock:
            if self._scheduler_status != SchedulerStatus.RUNNING:
                return -1
            if hard_stop:
                self.cancel_all()
            self._scheduler_status = SchedulerStatus.STOPPING
            last_event = Event(0, self.timefunc(), 0, None, (), {})
            if self._queue:
                last_event = max(self._queue)
            # we want to make sure the "terminating" event is the last one in the queue
            event = Event(0, last_event.time_, sys.maxsize, None, (), {})
            heapq.heappush(self._queue, event)
            self._notify()
        time.sleep(0)  # let other threads run since the next line is a join
        self._event_thread.join()
        with self._lock:
            self._scheduler_status = SchedulerStatus.STOPPED
        return 0
