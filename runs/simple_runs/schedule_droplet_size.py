from datetime import timedelta
from typing import Iterable

from unitpy import Unit, Quantity

from chembot.scheduler import JobSequence, JobConcurrent, Event
from chembot.scheduler.job_submitter import JobSubmitter
from chembot.equipment.valves import ValveServo
from chembot.equipment.pumps import SyringePumpHarvard
from chembot.equipment.sensors import PhaseSensor
from chembot.equipment.continuous_event_handler import ContinuousEventHandlerRepeatingNoEndSaving

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
            Event(  # here to stop alarm on pump if it is sounded
                resource=pump,
                callable_=SyringePumpHarvard.write_stop,
                duration=timedelta(milliseconds=1),
            )
        ]
    )


def job_fill_syringe_multiple(
        volume: Iterable[Quantity],
        flow_rate: Iterable[Quantity],
        valves: Iterable[str],
        pumps: Iterable[str],
) -> JobConcurrent:
    return JobConcurrent(
        [job_fill_syringe(vol, flow, val, p) for vol, flow, val, p in zip(volume, flow_rate, valves, pumps)],
    )


def job_flow_syringe_multiple(
        volume: Iterable[Quantity],
        flow_rate: Iterable[Quantity],
        valves: Iterable[str],
        pumps: Iterable[str],
        delay: timedelta = None
) -> JobConcurrent:
    return JobConcurrent(
        [job_flow(vol, flow, val, p) for vol, flow, val, p in zip(volume, flow_rate, valves, pumps)],
        delay=delay  # to allow syringes to stabilize
    )


def add_phase_sensor_calibration() -> JobSequence:
    return JobSequence(
        [
            Event(
                resource=NamesSensors.PHASE_SENSOR1,
                callable_=PhaseSensor.write_offset_voltage,
                duration=timedelta(seconds=0.2),
                kwargs={"offset_voltage": 2.907}  # oil=2.907, air = 2.65
            ),
            Event(
                resource=NamesSensors.PHASE_SENSOR1,
                callable_=PhaseSensor.write_gain,
                duration=timedelta(seconds=0.2),
                kwargs={"gain": 16}
            ),
            ]
    )


def add_phase_sensor(job: JobSequence | JobConcurrent) -> JobSequence:
    return JobSequence(
        [
            Event(
                resource=NamesSensors.PHASE_SENSOR1,
                callable_=PhaseSensor.write_continuous_event_handler,
                duration=timedelta(milliseconds=100),
                kwargs={
                    "event_handler":
                        ContinuousEventHandlerRepeatingNoEndSaving(
                            callable_=PhaseSensor.write_measure.__name__
                        )
                }
            ),
            job,
            Event(
                resource=NamesSensors.PHASE_SENSOR1,
                callable_=PhaseSensor.write_stop,
                duration=timedelta(milliseconds=1),
            )]
    )


def job_air_purge(volume: Quantity = 1 * Unit.ml, flow_rate: Quantity = 5 * Unit("ml/min")) -> JobSequence:
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
                kwargs={"position": "flow_air"}
            ),
            job_flow(volume, flow_rate, NamesValves.VALVE_BACK, NamesPump.PUMP_BACK)
        ]
    )


def fill_and_push(volume: list[Quantity], flow_rate: list[Quantity], valves: list[str], pumps: list[str]) \
        -> JobSequence:
    return JobSequence([
        job_fill_syringe_multiple(
            volume=volume,
            flow_rate=flow_rate,
            valves=valves,
            pumps=pumps
        ),
        job_flow_syringe_multiple(
            volume=volume,
            flow_rate=flow_rate,
            valves=valves,
            pumps=pumps
        ),
    ])


def job_droplets() -> JobSequence:
    return JobSequence(
        [
            # fill_and_push(
            #     volume=[0.001 * Unit.ml, 1 * Unit.ml],
            #     flow_rate=[1.5 * Unit("ml/min"), 1.5 * Unit("ml/min")],
            #     valves=[NamesValves.VALVE_FRONT, NamesValves.VALVE_MIDDLE],
            #     pumps=[NamesPump.PUMP_FRONT, NamesPump.PUMP_MIDDLE]
            # ),
            # add_phase_sensor_calibration(),
            # Event(
            #     resource=NamesSensors.PHASE_SENSOR1,
            #     callable_=PhaseSensor.write_auto_offset_gain,
            #     duration=timedelta(seconds=1),
            #     kwargs={"gain": 16}
            # ),

            # job_fill_syringe_multiple(
            #     volume=[1.0 * Unit.ml, (1.0/3 + 0.1) * Unit.ml],  # [1.2 * Unit.ml, (1.2/3 + 0.1) * Unit.ml]
            #     flow_rate=[3 * Unit("ml/min"), 1.5 * Unit("ml/min")],
            #     valves=[NamesValves.VALVE_FRONT, NamesValves.VALVE_MIDDLE],
            #     pumps=[NamesPump.PUMP_FRONT, NamesPump.PUMP_MIDDLE]
            # ),
            # priming
            # job_flow_syringe_multiple(
            #     volume=[0.03 * Unit.ml, 0.10 * Unit.ml],
            #     flow_rate=[0.5 * Unit("ml/min"), 0.5 * Unit("ml/min")],
            #     valves=[NamesValves.VALVE_FRONT, NamesValves.VALVE_MIDDLE],
            #     pumps=[NamesPump.PUMP_FRONT, NamesPump.PUMP_MIDDLE]
            # ),
            # Event(
            #     resource=NamesValves.VALVE_ANALYTICAL,
            #     callable_=ValveServo.write_move,
            #     duration=timedelta(seconds=1.5),
            #     kwargs={"position": "fill"}
            # ),
            job_flow_syringe_multiple(
                volume=[0.8 * Unit.ml, 0.8/3 * Unit.ml],
                flow_rate=[0.05 * Unit("ml/min"), 0.05 * Unit("ml/min")],
                valves=[NamesValves.VALVE_FRONT, NamesValves.VALVE_MIDDLE],
                pumps=[NamesPump.PUMP_FRONT, NamesPump.PUMP_MIDDLE],
                delay=timedelta(seconds=1)
            ),

            # main job
            # add_phase_sensor(
            #     job_flow_syringe_multiple(
            #         volume=[0.1 * Unit.ml, 0.1/3 * Unit.ml],
            #         flow_rate=[0.06 * Unit("ml/min"), 0.06/3 * Unit("ml/min")],
            #         valves=[NamesValves.VALVE_FRONT, NamesValves.VALVE_MIDDLE],
            #         pumps=[NamesPump.PUMP_FRONT, NamesPump.PUMP_MIDDLE]
            #     )
            # ),

            # fill_and_push(
            #     volume=[0.3 * Unit.ml],
            #     flow_rate=[1.5 * Unit("ml/min")],
            #     valves=[NamesValves.VALVE_FRONT],
            #     pumps=[NamesPump.PUMP_FRONT]
            # ),
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
