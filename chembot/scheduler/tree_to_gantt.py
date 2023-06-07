
import plotly.graph_objs as go

from chembot.scheduler.triggers import Trigger
from chembot.scheduler.event import Event, EventResource, EventCallable, EventNoOp
from chembot.scheduler.job import Job
from chembot.scheduler.vizualization.gantt_chart import Row, TimeBlock


def convert(job: Job) -> list[Row]:
    rows = get_rows(job)
    rows = list(rows)
    rows.sort()
    print(rows)


def get_rows(obj: Job | Event) -> set[str]:
    if isinstance(obj, Event):
        if isinstance(obj, EventCallable):
            return {obj.callable_.__name__, }
        if isinstance(obj, EventResource):
            return {obj.name, }
        if isinstance(obj, EventNoOp):
            return {obj.name, }
    if isinstance(obj, Job):
        set_ = set()
        for obj_ in obj.events:
            set_ = set_.union(get_rows(obj_))
        return set_

    raise ValueError("Not valid event.")
