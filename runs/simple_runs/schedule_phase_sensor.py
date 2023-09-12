from datetime import datetime, timedelta

import numpy as np

from chembot.scheduler import JobSequence, JobConcurrent, Event, Schedule
from chembot.scheduler.job_submitter import JobSubmitter
from chembot.equipment.sensors import PhaseSensor

from runs.launch_equipment.names import NamesSensors


def job_measure():
    return JobSequence(
        [
            Event(
                resource=NamesSensors.PHASE_SENSOR1,
                callable_=PhaseSensor.write_offset_voltage,
                duration=timedelta(seconds=0.2),
                kwargs={"offset_voltage": 2.7}
            ),
            Event(
                resource=NamesSensors.PHASE_SENSOR1,
                callable_=PhaseSensor.write_gain,
                duration=timedelta(seconds=0.2),
                kwargs={"gain": 16}
            ),
            Event(
                resource=NamesSensors.PHASE_SENSOR1,
                callable_=PhaseSensor.write_measure_continuously,
                duration=timedelta(seconds=10),
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
