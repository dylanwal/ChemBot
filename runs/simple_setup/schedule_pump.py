from datetime import datetime, timedelta

import numpy as np
from unitpy import Unit, Quantity

from chembot.scheduler import JobSequence, JobConcurrent, Event, Schedule
from chembot.equipment.pumps import SyringePumpHarvard
from chembot.scheduler.job_submitter import JobSubmitter
from chembot.equipment import Profile

from runs.individual_setup.equipment_names import NamesPump


# def sine_wave(x: np.ndarray) -> np.ndarray:
#     return np.sin(x.to(Unit.s)) * (Unit.mL / Unit.min)


def sine_wave(x: list[timedelta]) -> list[Quantity]:
    return [np.sin(x_.total_seconds()) * (Unit.ml/Unit.min) for x_ in x]


def job_flow_rate_function(time_: list[timedelta], flow_rate: list[Quantity],  delay: timedelta = None):
    flow_profile = Profile(SyringePumpHarvard.write_infusion_rate, ["flow_rate"], flow_rate, time_[1:])

    return JobSequence(
        [
            Event(NamesPump.PUMP_FRONT, SyringePumpHarvard.write_infusion_rate, timedelta(milliseconds=10),
                  kwargs={"profile": flow_profile}),
            Event(NamesPump.PUMP_FRONT, SyringePumpHarvard.write_run_infuse, timedelta(milliseconds=1)),
            Event(NamesPump.PUMP_FRONT, SyringePumpHarvard.write_infusion_rate, flow_profile.duration,
                  kwargs={"profile": flow_profile}),
            Event(NamesPump.PUMP_FRONT, SyringePumpHarvard.write_stop, timedelta(milliseconds=1)),
        ],
        name="function flow rate",
        delay=delay
    )


def job_infuse(volume: Quantity, flow_rate: Quantity) -> JobSequence:
    return JobSequence(
        [
            Event(
                resource=NamesPump.PUMP_FRONT,
                callable_=SyringePumpHarvard.write_infuse,
                duration=SyringePumpHarvard.compute_run_time(volume, flow_rate).to_timedelta(),
                kwargs={"flow_rate": flow_rate, "volume": volume}
            )
        ]
    )


def main():
    job_submitter = JobSubmitter()

    job = job_infuse(volume=1 * Unit.mL, flow_rate=0.5 * (Unit.mL / Unit.min))
    result = job_submitter.submit(job)
    print(result)

    # time_delta_array = Profile.linspace_timedelta(timedelta(0), timedelta(seconds=20), 20)
    # job2 = job_flow_rate_function(time_delta_array, flow_rate=sine_wave(time_delta_array))
    # result = job_submitter.submit(job2)
    # print(result)

    # full_schedule = job_submitter.get_schedule()
    # print(full_schedule)

    print("hi")


if __name__ == "__main__":
    main()
