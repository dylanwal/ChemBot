from datetime import timedelta
import time

from unitpy import Unit

from chembot.scheduler.triggers import Trigger, TriggerTimeAbsolute, TriggerTimeRelative, TriggerSignal, TriggerNow
from chembot.scheduler.event import EventCallable, EventResource
from chembot.scheduler.job import Job
from chembot.scheduler.resource import Resource
from chembot.scheduler.schedule import Schedule
from chembot.scheduler.schedular import Schedular
from chembot.scheduler.vizualization.job_tree import generate_job_flowchart, generate_trigger_flowchart

scheduler = Schedular()


class LED:
    def __init__(self, name: str):
        self.name = name

    def on(self):
        print("led on")

    def off(self):
        print("led off")


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


scheduler.schedule.add_resource(Resource("LED-red"))
scheduler.schedule.add_resource(Resource("valve"))
scheduler.schedule.add_resource(Resource("pump"))


##########################################################
def led_blink(time_: timedelta, trigger: Trigger = None, completion_signal: TriggerSignal = None):
    return Job(
        [
            EventResource("LED-red", LED.on.__name__, TriggerNow()),
            EventResource("LED-red", LED.off.__name__, TriggerTimeRelative(time_)),
        ],
        trigger=trigger,
        name=led_blink.__name__,
        completion_signal=completion_signal
    )


def refill_pump(vol: float, flow_rate: float, trigger: Trigger = None, completion_signal: TriggerSignal = None):
    trigger1 = TriggerSignal()
    trigger2 = TriggerSignal()

    return Job(
        [
            EventResource("valve", Valve.position.__name__, TriggerNow(), kwargs={"pos": 1},
                          completion_signal=trigger1),
            EventResource("pump", Pump.flow.__name__, trigger1, kwargs={"vol": vol, "flow_rate": flow_rate},
                          completion_signal=trigger2),
            EventResource("valve", Valve.position.__name__, trigger2, kwargs={"pos": 2}),
        ],
        name=refill_pump.__name__,
        trigger=trigger,
        completion_signal=completion_signal
    )


def reaction(vol: float, flow_rate: float, trigger: Trigger = None, completion_signal: TriggerSignal = None):
    trigger1 = TriggerSignal()

    return Job(
        [
            EventResource("LED-red", LED.on.__name__, TriggerNow()),
            EventResource("pump", Pump.flow.__name__, TriggerNow(), kwargs={"vol": vol, "flow_rate": flow_rate},
                          completion_signal=trigger1),
            EventResource("LED-red", LED.off.__name__, trigger1),
            refill_pump(vol=10, flow_rate=1, trigger=trigger1)
        ],
        name=reaction.__name__,
        trigger=trigger,
        completion_signal=completion_signal
    )

###################################################
trigger_refill_done = TriggerSignal()
trigger_reaction_done = TriggerSignal()

full_job = Job(
    [
        led_blink(timedelta(seconds=1)),
        refill_pump(1, 0.1, completion_signal=trigger_refill_done),
        reaction(1, 0.01, trigger=trigger_refill_done, completion_signal=trigger_reaction_done),
        led_blink(timedelta(seconds=1), trigger=trigger_reaction_done)
    ],
    name="full_job"
)

# print(generate_job_flowchart(full_job))
# print(generate_trigger_flowchart(full_job))
job_schedule = Schedule.from_job(full_job)
print(job_schedule)
#
# scheduler.validate(full_job)
# scheduler.next_time(full_job)

# scheduler.schedule.add_job(full_job)
# print(scheduler.schedule)
# chart = schedule_to_gantt_chart(scheduler.schedule)
# fig = create_gantt_chart(chart)
# fig.show()



