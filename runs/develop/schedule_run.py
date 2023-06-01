import time

from unitpy import Unit

from chembot.scheduler.triggers import TriggerTimeAbsolute, TriggerTimeRelative, TriggerSignal, TriggerNow
from chembot.scheduler.event import EventCallable, EventResource
from chembot.scheduler.job import Job
from chembot.scheduler.resource import Resource, ResourceGroup
from chembot.scheduler.base import Schedular

scheduler = Schedular()


def led_on():
    print("led on")


def led_off():
    print("led off")


led_blink = Job(
    [
        EventCallable(led_on, TriggerTimeRelative(3 * Unit.s), name="on"),
        EventCallable(led_off, TriggerTimeRelative(4 * Unit.s), name="off"),
    ],
    name="led_blink"
)


def led_rapid_pulse(arg):
    print(f"delay1: {arg}")
    time.sleep(arg)


def delay2(delay: int | float):
    print(f"delay2: {delay}")
    time.sleep(delay)


trigger1 = TriggerSignal("fish")

led_blink_long = Job(
    [
        EventCallable(led_on, TriggerNow(), name="on", completion_signal=trigger1.signal),
        EventCallable(led_off, trigger1, name="off"),
    ],
    name="led_blink_long"
)

job1 = Job([led_blink, led_blink_long])

# fig = plot_jobs(job1)
