from datetime import datetime, timedelta

import numpy as np

from chembot.scheduler import JobSequence, JobConcurrent, Event, Schedule
from chembot.scheduler.job_submitter import JobSubmitter
from chembot.equipment.sensors import PhaseSensor

from runs.individual_setup.names import NamesSensors


def job_measure(rate: float = 1/20):
    return JobSequence(
        [
            Event(
                resource=NamesSensors.PHASE_SENSOR1,
                callable_=PhaseSensor.write_measure_continuously,
                duration=timedelta(seconds=20),
                kwargs={"time_between_measurements": rate}
            ),
            Event(
                resource=NamesSensors.PHASE_SENSOR1,
                callable_=PhaseSensor.write_stop,
                duration=timedelta(milliseconds=1)
            ),
        ]
    )


def job_measure_phase(rate: float = 1/20):
    gas_background = np.array((48776, 36423, 35949, 27334, 30876, 30768, 50346, 28041), dtype="uint64")
    liquid_background = np.array((56157, 44772, 44267, 34047, 29480, 33828, 171358, 30869), dtype="uint64")

    return JobSequence(
        [
            Event(
                resource=NamesSensors.PHASE_SENSOR1,
                callable_=PhaseSensor.write_gas_background,
                duration=timedelta(milliseconds=1),
                kwargs={"gas_background": gas_background}
            ),
            Event(
                resource=NamesSensors.PHASE_SENSOR1,
                callable_=PhaseSensor.write_liquid_background,
                duration=timedelta(milliseconds=20),
                kwargs={"liquid_background": liquid_background}
            ),
            Event(
                resource=NamesSensors.PHASE_SENSOR1,
                callable_=PhaseSensor.write_measure_continuously,
                duration=timedelta(seconds=20),
                kwargs={"func": "write_measure_phase", "time_between_measurements": rate}
            ),
            Event(
                resource=NamesSensors.PHASE_SENSOR1,
                callable_=PhaseSensor.write_stop,
                duration=timedelta(milliseconds=1)
            ),
        ]
    )


def main():
    job_submitter = JobSubmitter()

    job = job_measure()
    result = job_submitter.submit(job)
    print(result)

    # full_schedule = job_submitter.get_schedule()
    # print(full_schedule)

    print("hi")


if __name__ == "__main__":
    main()
