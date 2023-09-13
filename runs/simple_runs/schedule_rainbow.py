from datetime import datetime, timedelta
import colorsys

import numpy as np

from chembot.scheduler import JobSequence, JobConcurrent, Event, Schedule
from chembot.equipment.lights import LightPico
from chembot.scheduler.job_submitter import JobSubmitter
from chembot.equipment import ContinuousEventHandler

from chembot.scheduler.vizualization.job_tree import generate_job_flowchart
from chembot.scheduler.vizualization.gantt_chart_app import create_app
from chembot.scheduler.vizualization.schedule_to_gantt_chart import schedule_to_gantt_chart

from runs.launch_equipment.names import NamesLEDColors


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
    time_delta_array = ContinuousEventHandler.linspace_timedelta(timedelta(0), duration, n)

    # power is [0, 65535] and color is [0, 255] so divide by 255
    red = np.round(color_array[:, 0] / 255 * power).astype("uint16").tolist()
    green = np.round(color_array[:, 1] / 255 * power).astype("uint16").tolist()
    blue = np.round(color_array[:, 2] / 255 * power).astype("uint16").tolist()

    red_profile = ContinuousEventHandler(LightPico.write_power, ["power"], red, time_delta_array)
    green_profile = ContinuousEventHandler(LightPico.write_power, ["power"], green, time_delta_array)
    blue_profile = ContinuousEventHandler(LightPico.write_power, ["power"], blue, time_delta_array)

    return JobSequence(
        [
            JobConcurrent(
                [
                    Event(NamesLEDColors.DEEP_RED, LightPico.write_profile, red_profile.duration,
                          kwargs={"profile": red_profile}),
                    Event(NamesLEDColors.GREEN, LightPico.write_profile, green_profile.duration,
                          kwargs={"profile": green_profile}),
                    Event(NamesLEDColors.BLUE, LightPico.write_profile, blue_profile.duration,
                          kwargs={"profile": blue_profile}),
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


def main():
    job_submitter = JobSubmitter()

    job = rainbow_job(n=300, duration=timedelta(seconds=30), power=656)
    result = job_submitter.submit(job)
    print(result)

    # full_schedule = job_submitter.get_schedule()
    # print(full_schedule)

    # gantt_chart = schedule_to_gantt_chart(full_schedule.schedule)
    # app = create_app(gantt_chart)
    # app.run(debug=True)

    print("hi")


if __name__ == "__main__":
    main()
