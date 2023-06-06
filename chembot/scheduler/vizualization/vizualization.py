
import plotly.graph_objs as go

from chembot.scheduler.triggers import Trigger
from chembot.scheduler.event import Event, EventResource, EventCallable, EventNoOp
from chembot.scheduler.job import Job
from chembot.scheduler.vizualization.gantt_chart import Row, TimeBlock



def convert(job: Job) -> list[Row]:
    rows = get_rows(Job)
    set time
    create timeblocks



def get_rows(event: Job | Event) -> list[str]:
    if isinstance(event, Event):
        if isinstance(event, EventCallable):
            return event.callable_.__name__
        if isinstance(event, EventResource):
            return event.name
        if isinstance(event, EventNoOp):
            return event.name
