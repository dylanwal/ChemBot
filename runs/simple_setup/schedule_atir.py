from datetime import datetime, timedelta

from chembot.scheduler import JobSequence, JobConcurrent, Event, Schedule
from chembot.scheduler.job_submitter import JobSubmitter
from chembot.equipment.sensors import ATIR

from runs.individual_setup.names import NamesSensors


def job_rotate_through_all_positions() -> JobSequence:
    return JobSequence(
        [
            Event(
                resource=NamesSensors.ATIR,
                callable_=ATIR.write_background,
                duration=timedelta(seconds=15),
            ),
            Event(
                resource=NamesSensors.ATIR,
                callable_=ATIR.write_measure,
                duration=timedelta(seconds=15),
            )
        ]
    )


def main():
    job_submitter = JobSubmitter()

    job = job_rotate_through_all_positions()
    result = job_submitter.submit(job)
    print(result)

    # full_schedule = job_submitter.get_schedule()
    # print(full_schedule)

    print("hi")


if __name__ == "__main__":
    main()
