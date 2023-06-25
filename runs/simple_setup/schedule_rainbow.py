from datetime import datetime, timedelta
import colorsys

from chembot.scheduler import JobSequence, JobConcurrent, Event, Schedule
from chembot.equipment.lights import LightPico
from chembot.scheduler.job_submitter import JobSubmitter
from chembot.equipment import Profile

from chembot.scheduler.vizualization.job_tree import generate_job_flowchart
from chembot.scheduler.vizualization.gantt_chart_app import create_app
from chembot.scheduler.vizualization.schedule_to_gantt_chart import schedule_to_gantt_chart

from runs.individual_setup.equipment_names import LEDColors, Serial


def rainbow(n: int) -> list[list[int, int, int], ...]:
    """ List[List[red, green, blue], ...]   range: 0 to 255"""
    result = []
    step = 1/n

    for i in range(n):
        (r, g, b) = colorsys.hsv_to_rgb(i*step, 1.0, 1.0)
        result.append([int(255 * r), int(255 * g), int(255 * b)])

    return result


def rainbow_job(n: int, duration: timedelta, delay: timedelta = None):
    color_array = rainbow(n)
    time_delta_array = Profile.linspace_timedelta(timedelta(0), duration, n)

    # power is [0, 100] and color is [0, 255] so divide by 255
    red = [color[0]/255 for color in color_array]
    green = [color[1]/255 for color in color_array]
    blue = [color[2]/255 for color in color_array]

    red_profile = Profile(LightPico.write_power, ["power"], red, time_delta_array)
    green_profile = Profile(LightPico.write_power, ["power"], green, time_delta_array)
    blue_profile = Profile(LightPico.write_power, ["power"], blue, time_delta_array)

    return JobConcurrent(
        [
            Event(LEDColors.DEEP_RED, LightPico.write_profile, red_profile.duration, kwargs={"profile": red_profile}),
            Event(LEDColors.GREEN, LightPico.write_profile, green_profile.duration, kwargs={"profile": red_profile}),
            Event(LEDColors.BLUE, LightPico.write_profile, blue_profile.duration, kwargs={"profile": red_profile}),
        ],
        delay=delay,
        name="rainbow"
    )


def main():
    job_submitter = JobSubmitter()

    job = rainbow_job(n=100, duration=timedelta(seconds=10))
    result = job_submitter.submit(job)
    print(result)

    # full_schedule = job_submitter.get_schedule()
    # print(full_schedule)
    # gantt_chart = schedule_to_gantt_chart(full_schedule.schedule)
    # app = create_app(gantt_chart)
    # app.run(debug=True)

    print("hi")


if __name__ is "__main__":
    main()
