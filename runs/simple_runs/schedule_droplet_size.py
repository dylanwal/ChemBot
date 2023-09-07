from datetime import timedelta
from typing import Iterable

from unitpy import Unit, Quantity

from chembot.scheduler import JobSequence, JobConcurrent, Event
from chembot.scheduler.job_submitter import JobSubmitter
from chembot.equipment.valves import ValveServo
from chembot.equipment.pumps import SyringePumpHarvard
from chembot.equipment.sensors import PhaseSensor

from runs.launch_equipment.names import NamesPump, NamesValves, NamesSensors


def job_flow(volume: Quantity, flow_rate: Quantity, valve: str, pump: str) -> JobSequence:
    return JobSequence(
        [
            Event(
                resource=valve,
                callable_=ValveServo.write_move,
                duration=timedelta(seconds=1.5),
                kwargs={"position": "flow"}
            ),
            Event(
                resource=pump,
                callable_=SyringePumpHarvard.write_infuse,
                duration=SyringePumpHarvard.compute_run_time(volume, flow_rate).to_timedelta(),
                kwargs={"volume": volume, "flow_rate": flow_rate}
            ),
            Event(  # here to stop alarm on pump if it is sounded
                resource=pump,
                callable_=SyringePumpHarvard.write_stop,
                duration=timedelta(milliseconds=1),
            )
        ]
    )


def job_fill_syringe(volume: Quantity, flow_rate: Quantity, valve: str, pump: str) -> JobSequence:
    return JobSequence(
        [
            Event(
                resource=valve,
                callable_=ValveServo.write_move,
                duration=timedelta(seconds=1.5),
                kwargs={"position": "fill"}
            ),
            Event(
                resource=pump,
                callable_=SyringePumpHarvard.write_withdraw,
                duration=SyringePumpHarvard.compute_run_time(volume, flow_rate).to_timedelta(),
                kwargs={"volume": volume, "flow_rate": flow_rate}
            ),
        ]
    )


def job_fill_syringe_multiple(
        volume: Iterable[Quantity],
        flow_rate: Iterable[Quantity],
        valves: Iterable[str],
        pumps: Iterable[str]
            ) -> JobConcurrent:
    return JobConcurrent(
        [job_fill_syringe(vol, flow, val, p) for vol, flow, val, p in zip(volume, flow_rate, valves, pumps)]
    )


def job_flow_syringe_multiple(
        volume: Iterable[Quantity],
        flow_rate: Iterable[Quantity],
        valves: Iterable[str],
        pumps: Iterable[str]
            ) -> JobConcurrent:
    return JobConcurrent(
        [job_flow(vol, flow, val, p) for vol, flow, val, p in zip(volume, flow_rate, valves, pumps)]
    )


def add_phase_sensor(job: JobSequence | JobConcurrent) -> JobSequence:
    return JobSequence(
        [
            Event(
                resource=NamesSensors.PHASE_SENSOR1,
                callable_=PhaseSensor.write_measure_continuously,
                duration=timedelta(milliseconds=100),
                kwargs={"func": "write_measure"}
            ),
            job,
            Event(
                resource=NamesSensors.PHASE_SENSOR1,
                callable_=PhaseSensor.write_stop,
                duration=timedelta(milliseconds=1),
            )]
    )


def job_air_purge(volume: Quantity = 2 * Unit.ml, flow_rate: Quantity = 5 * Unit("ml/min")) -> JobSequence:
    return JobSequence(
        [
            job_fill_syringe(volume, flow_rate, NamesValves.VALVE_BACK, NamesPump.PUMP_BACK),
            Event(
                resource=NamesValves.VALVE_FRONT,
                callable_=ValveServo.write_move,
                duration=timedelta(seconds=1.5),
                kwargs={"position": "fill"}
            ),
            Event(
                resource=NamesValves.VALVE_MIDDLE,
                callable_=ValveServo.write_move,
                duration=timedelta(seconds=1.5),
                kwargs={"position": "fill"}
            ),
            job_flow(volume, flow_rate, NamesValves.VALVE_BACK, NamesPump.PUMP_BACK)
        ]
    )


def job_droplets() -> JobSequence:
    return JobSequence(
        [
            job_fill_syringe_multiple(
                volume=[2 * Unit.ml, 0.5 * Unit.ml],
                flow_rate=[1.5 * Unit("ml/min"), 1.5 * Unit("ml/min")],
                valves=[NamesValves.VALVE_FRONT, NamesValves.VALVE_MIDDLE],
                pumps=[NamesPump.PUMP_FRONT, NamesPump.PUMP_MIDDLE]
            ),
            # priming
            job_flow_syringe_multiple(
                volume=[2 * Unit.ml, 0.5 * Unit.ml],
                flow_rate=[1.5 * Unit("ml/min"), 1.5 * Unit("ml/min")],
                valves=[NamesValves.VALVE_FRONT, NamesValves.VALVE_MIDDLE],
                pumps=[NamesPump.PUMP_FRONT, NamesPump.PUMP_MIDDLE]
            ),
            # main job
            add_phase_sensor(
                job_flow_syringe_multiple(
                    volume=[2 * Unit.ml, 0.5 * Unit.ml],
                    flow_rate=[1.5 * Unit("ml/min"), 1.5 * Unit("ml/min")],
                    valves=[NamesValves.VALVE_FRONT, NamesValves.VALVE_MIDDLE],
                    pumps=[NamesPump.PUMP_FRONT, NamesPump.PUMP_MIDDLE]
                )
            ),
            # job_air_purge(),
        ]
    )


def main():
    job_submitter = JobSubmitter()
    result = job_submitter.submit(job_droplets())
    print(result)

    # full_schedule = job_submitter.get_schedule()
    # print(full_schedule)

    print("hi")


if __name__ == "__main__":
    main()
