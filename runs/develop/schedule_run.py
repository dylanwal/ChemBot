import time

from unitpy import Unit

from chembot.scheduler.triggers import Trigger, TriggerTimeAbsolute, TriggerTimeRelative, TriggerSignal, TriggerNow
from chembot.scheduler.event import EventCallable, EventResource
from chembot.scheduler.job import Job
from chembot.scheduler.resource import Resource, ResourceGroup
from chembot.scheduler.base import Schedular
from chembot.scheduler.tree_to_gantt import convert

scheduler = Schedular()


def led_on():
    print("led on")


def led_off():
    print("led off")


def valve_position(pos: int):
    print(f"valve position: {pos}")
    time.sleep(0.5)


def pump_flow(vol: int | float, flow_rate: float):
    print(f"pump flow: {vol}; {flow_rate}")
    time.sleep(1)


##########################################################
def led_blink(time_: float, trigger: Trigger = None):
    return Job(
        [
            EventCallable(led_on, TriggerNow(), name="on"),
            EventCallable(led_off, TriggerTimeRelative(time_), name="off"),
        ],
        trigger=trigger,
        name=led_blink.__name__
    )


def refill_pump(vol: float, flow_rate: float, trigger: Trigger = None, completion_signal: TriggerSignal = None):
    trigger1 = TriggerSignal()
    trigger2 = TriggerSignal()

    return Job(
        [
            EventCallable(valve_position, TriggerNow(), kwargs={"pos": 1}, completion_signal=trigger1),
            EventCallable(pump_flow, trigger1, kwargs={"vol": vol, "flow_rate": flow_rate}, name="off",
                          completion_signal=trigger2),
            EventCallable(valve_position, trigger2, kwargs={"pos": 2}, completion_signal=completion_signal),
        ],
        name=refill_pump.__name__,
        trigger=trigger
    )


###################################################
trigger_refill_done = TriggerSignal()

full_job = Job(
    [
        led_blink(1),
        refill_pump(1, 0.1, completion_signal=trigger_refill_done),
        led_blink(1, trigger=trigger_refill_done)
    ],
    name="full_job"
)

convert(full_job)
