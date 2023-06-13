from datetime import timedelta, datetime
import time

from unitpy import Quantity, Unit

from chembot.scheduler.event import EventResource
from chembot.scheduler.job import JobSequence, JobConcurrent
from chembot.scheduler.resource import Resource
from chembot.scheduler.schedule import Schedule
from chembot.scheduler.schedular import Schedular
from chembot.scheduler.vizualization.job_tree import generate_job_flowchart
from chembot.scheduler.vizualization.schedule_to_gantt_chart import schedule_to_gantt_chart
from chembot.scheduler.vizualization.gantt_chart_plot import create_gantt_chart
from chembot.scheduler.vizualization.gantt_chart_app import create_app

scheduler = Schedular()


class LED:
    def __init__(self, name: str):
        self.name = name

    @property
    def tt(self):
        return "tt"

    def on(self):
        print("led on")

    def off(self):
        print("led off")

    def duration(self, duration: timedelta):
        self.on()
        # duration
        self.off()


class Valve:
    def __init__(self, name: str):
        self.name = name

    def position(self, pos: int):
        print(f"valve position: {pos}")
        time.sleep(0.5)


class Pump:
    def __init__(self, name: str):
        self.name = name

    def flow(self, vol: int | float, flow_rate: float):
        print(f"pump flow: {vol}; {flow_rate}")
        time.sleep(1)

    @staticmethod
    def calculate_duration(volume: Quantity, flow_rate: Quantity) -> timedelta:
        if volume.unit.dimensionality != Unit("L").dimensionality:
            raise ValueError(f"'volume' must have a volume unit. Given: {volume.dimensionality}")
        if flow_rate.unit.dimensionality != Unit("L/min").dimensionality:
            raise ValueError(f"'flow rate' must have a volume unit. Given: {flow_rate.dimensionality}")

        return timedelta(minutes=(volume/flow_rate).to("min").value)


scheduler.schedule.add_resource(Resource("LED-red"))
scheduler.schedule.add_resource(Resource("valve"))
scheduler.schedule.add_resource(Resource("pump"))


##########################################################
def refill_pump(vol: Quantity, flow_rate: Quantity):
    return JobSequence(
        [
            EventResource("valve", Valve.position.__name__, timedelta(milliseconds=100), kwargs={"pos": 1}),
            EventResource("pump", Pump.flow.__name__, Pump.calculate_duration(vol, flow_rate),
                          kwargs={"vol": vol, "flow_rate": flow_rate}),
            EventResource("valve", Valve.position.__name__, timedelta(milliseconds=100), kwargs={"pos": 2}),
        ],
        name=refill_pump.__name__
    )


def reaction(vol: Quantity, flow_rate: Quantity):
    duration = Pump.calculate_duration(vol, flow_rate)

    return JobConcurrent(
        [
            EventResource("LED-red", LED.duration.__name__, duration, kwargs={"duration": duration}),
            EventResource("pump", Pump.flow.__name__, duration, kwargs={"vol": vol, "flow_rate": flow_rate}),
        ],
        name=reaction.__name__,
    )


def grouping():
    duration = timedelta(seconds=1)
    return JobConcurrent(
        [
            EventResource("LED-red", LED.duration.__name__, duration, kwargs={"duration": duration},
                          delay=timedelta(seconds=0.5)),
            refill_pump(1 * Unit.mL, 0.5 * Unit("mL/min")),
        ],
        name="grouping"
    )


###################################################
full_job = JobSequence(
    [
        grouping(),
        reaction(1 * Unit.mL, 0.1 * Unit("mL/min")),
        grouping()
    ],
    time_start=datetime(year=2023, month=1, day=1, hour=1, minute=1),
    name="full_job"
)

print(generate_job_flowchart(full_job))
job_schedule = Schedule.from_job(full_job)

chart = schedule_to_gantt_chart(job_schedule)
# fig = create_gantt_chart(chart)
# fig.write_html("temp.html", auto_open=True)

app = create_app(chart)
app.run_server(debug=True)

# scheduler.validate(full_job)
# scheduler.next_time(full_job)
