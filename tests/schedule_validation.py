from datetime import datetime, timedelta
import colorsys

from chembot.scheduler import JobSequence, Event, Job, Schedule, JobSubmitResult, JobConcurrent
from chembot.scheduler.validate import validate_schedule
from chembot.equipment.lights import LightPico
from chembot.communication.serial_pico import PicoSerial
from chembot.equipment.equipment_interface import EquipmentRegistry
from chembot.equipment.continuous_event_handler import ContinuousEventHandler


def example_schedule() -> Job:
    return JobSequence(
        [
            Event("on_board_LED", LightPico.write_off, timedelta(milliseconds=10)),
            Event("on_board_LED", LightPico.write_on, timedelta(milliseconds=10), delay=timedelta(seconds=10)),
            rainbow_job(n=100, duration=timedelta(seconds=10))
        ]
    )


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
    time_delta_array = ContinuousEventHandler.linspace_timedelta(timedelta(0), duration, n)

    # power is [0, 100] and color is [0, 255] so divide by 255
    red = [int(color[0]/255*100) for color in color_array]
    green = [int(color[1]/255*100) for color in color_array]
    blue = [int(color[2]/255*100) for color in color_array]

    red_profile = ContinuousEventHandler(LightPico.write_power, ["power"], red, time_delta_array)
    green_profile = ContinuousEventHandler(LightPico.write_power, ["power"], green, time_delta_array)
    blue_profile = ContinuousEventHandler(LightPico.write_power, ["power"], blue, time_delta_array)

    return JobConcurrent(
        [
            Event("red", LightPico.write_profile, red_profile.duration, kwargs={"profile": red_profile}),
            Event("green", LightPico.write_profile, green_profile.duration, kwargs={"profile": red_profile}),
            Event("blue", LightPico.write_profile, blue_profile.duration, kwargs={"profile": red_profile}),
        ],
        delay=delay,
        name="rainbow"
    )


def main():
    job = example_schedule()
    job.time_start = datetime.now()
    schedule = Schedule.from_job(job)
    result = JobSubmitResult(job.id_)
    registry = EquipmentRegistry()
    registry.register_equipment("on_board_LED", LightPico)
    registry.register_equipment("pico_serial", PicoSerial)
    registry.register_equipment("red", LightPico)
    registry.register_equipment("green", LightPico)
    registry.register_equipment("blue", LightPico)

    validate_schedule(schedule, registry, result)

    print(result)


if __name__ == "__main__":
    main()
