from datetime import timedelta
import colorsys

import numpy as np

from chembot.scheduler import JobSequence, JobConcurrent, Event
from chembot.equipment.lights import LightPico
from chembot.scheduler.job_submitter import JobSubmitter
from chembot.equipment import ContinuousEventHandlerProfile


from runs.launch_equipment.names import NamesLEDColors


def blink(on_time: timedelta, delay: timedelta = None, led_name: str = NamesLEDColors.GREEN):
    kwargs = {"power": 10_000}
    return JobSequence(
        [
            Event(led_name, LightPico.write_power, timedelta(milliseconds=10), kwargs=kwargs),
            Event(led_name, LightPico.write_off, timedelta(milliseconds=10), delay=on_time),
        ],
        delay=delay,
        name="blink"
    )


def triple_blink(on_time: timedelta, off_time: timedelta, led: str = NamesLEDColors.GREEN):
    return JobSequence(
        [
            blink(on_time, led_name=led),
            blink(on_time, off_time, led_name=led),
            blink(on_time, off_time, led_name=led)
        ],
        name="triple_blink"
    )


def rainbow(n: int) -> list[list[int, int, int], ...]:
    """ List[List[red, green, blue], ...]   range: 0 to 255"""
    result = []
    step = 1 / n

    for i in range(n):
        (r, g, b) = colorsys.hsv_to_rgb(i * step, 1.0, 1.0)
        result.append([int(255 * r), int(255 * g), int(255 * b)])

    return result


def rainbow_job(n: int, duration: timedelta, power: int = 65535, delay: timedelta = None):
    color_array = np.array(rainbow(n), dtype="uint8")
    time_delta_array = np.ones((n, 1)) * (duration.total_seconds() / n)

    # power is [0, 65535] and color is [0, 255] so divide by 255
    red = np.round(color_array[:, 0] / 255 * power).astype("uint16")
    green = np.round(color_array[:, 1] / 255 * power).astype("uint16")
    blue = np.round(color_array[:, 2] / 255 * power).astype("uint16")

    red_profile = ContinuousEventHandlerProfile(LightPico.write_power, ["power"], red, time_delta_array)
    green_profile = ContinuousEventHandlerProfile(LightPico.write_power, ["power"], green, time_delta_array)
    blue_profile = ContinuousEventHandlerProfile(LightPico.write_power, ["power"], blue, time_delta_array)

    return JobSequence(
        [
            JobConcurrent(
                [
                    Event(
                        resource=NamesLEDColors.DEEP_RED,
                        callable_=LightPico.write_continuous_event_handler,
                        duration=timedelta(milliseconds=100),
                        kwargs={"event_handler": red_profile},
                    ),
                    Event(
                        resource=NamesLEDColors.GREEN,
                        callable_=LightPico.write_continuous_event_handler,
                        duration=timedelta(milliseconds=100),
                        kwargs={"event_handler": green_profile},
                    ),
                    Event(
                        resource=NamesLEDColors.BLUE,
                        callable_=LightPico.write_continuous_event_handler,
                        duration=timedelta(milliseconds=100),
                        kwargs={"event_handler": blue_profile},
                    ),
                ],
                delay=delay,
                name="rainbow"
            ),
            JobConcurrent(
                [
                    Event(NamesLEDColors.DEEP_RED, LightPico.write_off, timedelta(microseconds=100)),
                    Event(NamesLEDColors.GREEN, LightPico.write_off, timedelta(microseconds=100)),
                    Event(NamesLEDColors.BLUE, LightPico.write_off, timedelta(microseconds=100)),
                ],
                delay=timedelta(milliseconds=100),
                name="turn_off"
            ),
        ],
        name="full rainbow sequence"
    )


def linear_job(n: int = 100, duration: timedelta = timedelta(seconds=10), led_name: str = NamesLEDColors.GREEN,
               power_min: int = 0, power_max: int = 65535):
    # power is [0, 65535]
    lin_space = np.linspace(power_min, power_max, n, dtype=np.uint32)
    time_delta_array = np.linspace(0, duration.total_seconds(), n)

    profile = ContinuousEventHandlerProfile(LightPico.write_power, ["power"], lin_space, time_delta_array)
    return JobSequence(
        [
            Event(
                resource=led_name,
                callable_=LightPico.write_continuous_event_handler,
                duration=timedelta(milliseconds=100),
                kwargs={"event_handler": profile},
            ),
            Event(led_name, LightPico.write_stop, timedelta(microseconds=100), delay=duration)

        ],
        name="linear_sweep"
    )


def main():
    job_submitter = JobSubmitter()

    job = triple_blink(on_time=timedelta(seconds=1), off_time=timedelta(seconds=2), led=NamesLEDColors.DEEP_RED)  #TODO: issue with schedualr
    # job = rainbow_job(n=100, duration=timedelta(seconds=10), power=656)
    # job = linear_job(n=20, duration=timedelta(seconds=10), power_max=6553)  # [0:1:65535]
    result = job_submitter.submit(job)
    print(result)

    # full_schedule = job_submitter.get_schedule()
    # print(full_schedule)

    print("hi")


if __name__ == "__main__":
    main()
