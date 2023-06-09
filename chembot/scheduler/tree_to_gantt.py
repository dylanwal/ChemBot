from chembot.scheduler.event import Event, EventResource, EventCallable, EventNoOp
from chembot.scheduler.job import Job
from chembot.scheduler.gantt_chart import GanttChart, Row, TimeBlock


def convert(job: Job) -> GanttChart:
    gantt_chart = GanttChart()
    loop_through_jobs(gantt_chart, job)
    return gantt_chart


def loop_through_jobs(gantt_chart: GanttChart, obj: Job | Event):
    if isinstance(obj, Event):
        if isinstance(obj, EventCallable):
            gantt_chart.add_time_block(obj.callable_.__name__, obj)
        elif isinstance(obj, EventResource):
            gantt_chart.add_time_block(obj.resource, obj)
        elif isinstance(obj, EventNoOp):
            gantt_chart.add_time_block(obj.name, obj)
    elif isinstance(obj, Job):
        for obj_ in obj.events:
            loop_through_jobs(gantt_chart, obj_)
    else:
        raise ValueError("Not valid event.")
