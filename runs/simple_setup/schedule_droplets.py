from datetime import datetime, timedelta

from unitpy import Unit, Quantity

from chembot.scheduler import JobSequence, JobConcurrent, Event, Schedule
from chembot.scheduler.job_submitter import JobSubmitter
from chembot.equipment.valves import ValveServo
from chembot.equipment.pumps import SyringePumpHarvard

from runs.individual_setup.names import NamesPump, NamesValves


def job_flow(volume: Quantity, flow_rate: Quantity):
    return JobSequence(
        [
            _valves(),
            _flow(volume, flow_rate)
        ]
    )


def _valves() -> JobConcurrent:
    return JobConcurrent(
        [
            Event(
                resource=NamesValves.VALVE_BACK,
                callable_=ValveServo.write_move,
                duration=timedelta(seconds=1.5),
                kwargs={"position": "flow"}
            ),
            Event(
                resource=NamesValves.VALVE_MIDDLE,
                callable_=ValveServo.write_move,
                duration=timedelta(seconds=1.5),
                kwargs={"position": "flow"}
            ),
            Event(
                resource=NamesValves.VALVE_FRONT,
                callable_=ValveServo.write_move,
                duration=timedelta(seconds=1.5),
                kwargs={"position": "flow"}
            ),
        ]
    )


def _flow(volume: Quantity, flow_rate: Quantity) -> JobConcurrent:
    return JobConcurrent(
        [
            Event(
                resource=NamesPump.PUMP_BACK,
                callable_=SyringePumpHarvard.write_infuse,
                duration=SyringePumpHarvard.compute_run_time(volume, flow_rate).to_timedelta(),
                kwargs={"volume": volume, "flow_rate": flow_rate}
            ),
            Event(
                resource=NamesPump.PUMP_FRONT,
                callable_=SyringePumpHarvard.write_infuse,
                duration=SyringePumpHarvard.compute_run_time(volume, flow_rate).to_timedelta(),
                kwargs={"volume": volume, "flow_rate": flow_rate}
            )
        ]
    )


def job_fill_back():
    return JobSequence(
        [
            Event(
                resource=NamesValves.VALVE_BACK,
                callable_=ValveServo.write_move,
                duration=timedelta(seconds=1.5),
                kwargs={"position": "fill"}
            ),
            Event(
                resource=NamesPump.PUMP_BACK,
                callable_=SyringePumpHarvard.write_refill,
                duration=timedelta(minutes=3),
            ),
        ]
    )


def job_fill_front():
    return JobSequence(
        [
            Event(
                resource=NamesValves.VALVE_FRONT,
                callable_=ValveServo.write_move,
                duration=timedelta(seconds=1.5),
                kwargs={"position": "fill"}
            ),
            Event(
                resource=NamesPump.PUMP_FRONT,
                callable_=SyringePumpHarvard.write_refill,
                duration=timedelta(minutes=3),
            ),
        ]
    )


def job_fill() -> JobConcurrent:
    return JobConcurrent(
        [
            job_fill_back(),
            job_fill_front()
        ]
    )


def job_air_purge() -> JobSequence:
    return JobSequence(
        [
            job_fill_back(),
            Event(
                resource=NamesValves.VALVE_BACK,
                callable_=ValveServo.write_move,
                duration=timedelta(seconds=1.5),
                kwargs={"position": "flow"}
            ),
        ]
    )


def job_droplets(volume: Quantity, flow_rate: Quantity) -> JobSequence:
    return JobSequence(
        [
            job_fill(),
            job_flow(volume, flow_rate),
            job_air_purge(),
            job_air_purge()
        ]
    )


def main():
    job_submitter = JobSubmitter()

    job = job_droplets(volume=0.3 * Unit.mL, flow_rate=0.1 * (Unit.mL / Unit.min))
    result = job_submitter.submit(job)
    print(result)

    # full_schedule = job_submitter.get_schedule()
    # print(full_schedule)

    print("hi")


if __name__ == "__main__":
    main()
