from datetime import datetime, timedelta

from chembot.scheduler import JobSequence, JobConcurrent, Event, Schedule
from chembot.equipment.valves import ValveServo
from chembot.scheduler.job_submitter import JobSubmitter

from runs.individual_setup.names import NamesValves


def job_rotate_through_all_positions() -> JobSequence:
    return JobSequence(
        [
            Event(
                resource=NamesValves.VALVE_BACK,
                callable_=ValveServo.write_move_next,
                duration=timedelta(seconds=3),
            ),
            Event(
                resource=NamesValves.VALVE_BACK,
                callable_=ValveServo.write_move_next,
                duration=timedelta(seconds=3),
            ),
            Event(
                resource=NamesValves.VALVE_BACK,
                callable_=ValveServo.write_move_next,
                duration=timedelta(seconds=3),
            ),
            Event(
                resource=NamesValves.VALVE_BACK,
                callable_=ValveServo.write_move_next,
                duration=timedelta(seconds=3),
            ),
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
