from datetime import datetime, timedelta

from unitpy import Unit

from chembot.scheduler import JobSequence, JobConcurrent, Event, Schedule
from chembot.equipment.continuous_event_handler import ContinuousEventHandlerRepeatingNoEndSaving
from chembot.scheduler.job_submitter import JobSubmitter
from chembot.equipment.temperature_control import PolyRecirculatingBath

from runs.launch_equipment.names import NamesEquipment


def read_temperature(duration: timedelta):
    return JobSequence(
        [
            Event(
                resource=NamesEquipment.BATH,
                callable_=PolyRecirculatingBath.write_continuous_event_handler,
                duration=timedelta(milliseconds=100),
                kwargs={
                    "event_handler":
                        ContinuousEventHandlerRepeatingNoEndSaving(
                            callable_=PolyRecirculatingBath.read_temperature.__name__
                        )
                }
            ),
            Event(
                resource=NamesEquipment.BATH,
                callable_=PolyRecirculatingBath.write_stop,
                duration=timedelta(milliseconds=100),
                delay=duration
            )
        ]
    )


def job_temperature_cycle() -> JobSequence:
    return JobSequence(
        [
            Event(
                resource=NamesEquipment.BATH,
                callable_=PolyRecirculatingBath.write_set_point,
                duration=timedelta(seconds=1),
                kwargs={"temperature": 5 * Unit.degC}
            ),
            read_temperature(timedelta(minutes=60)),
        ]
    )


def main():
    job_submitter = JobSubmitter()

    job = job_temperature_cycle()
    job.name = "test_bath"
    result = job_submitter.submit(job)
    print(result)


if __name__ == "__main__":
    main()
