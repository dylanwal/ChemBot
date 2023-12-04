from datetime import timedelta
from typing import Iterable

from unitpy import Unit, Quantity

from chembot.scheduler import JobSequence, JobConcurrent, Event
from chembot.scheduler.job_submitter import JobSubmitter
from chembot.equipment.valves import ValveServo
from chembot.equipment.pumps import SyringePumpHarvard
from chembot.equipment.sensors import PhaseSensor, ATIR, NMR
from chembot.equipment.temperature_control import PolyRecirculatingBath
from chembot.equipment.continuous_event_handler import ContinuousEventHandlerRepeatingNoEndSaving

from runs.launch_equipment.names import NamesPump, NamesValves, NamesSensors, NamesEquipment


def job_flow(volume: Quantity, flow_rate: Quantity, valve: str, pump: str) -> JobSequence:
    flow_time = SyringePumpHarvard.compute_run_time(volume, flow_rate).to_timedelta()
    force_delay = timedelta(seconds=30)
    flow_time = flow_time - force_delay
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
                duration=timedelta(seconds=0.1),
                kwargs={"volume": volume, "flow_rate": flow_rate}
            ),
            Event(
                resource=pump,
                callable_=SyringePumpHarvard.write_force,
                duration=timedelta(seconds=0.1),
                kwargs={"force": 40},
                delay=force_delay
            ),
            Event(  # here to stop alarm on pump if it is sounded
                resource=pump,
                callable_=SyringePumpHarvard.write_stop,
                duration=timedelta(milliseconds=1),
                delay=flow_time
            )
        ]
    )


def job_fill_syringe(volume: Quantity, flow_rate: Quantity, valve: str, pump: str) -> JobSequence:
    extra_volume = 0.3 * Unit.ml
    volume = volume + extra_volume
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
            Event(
                resource=pump,
                callable_=SyringePumpHarvard.write_infuse,
                duration=SyringePumpHarvard.compute_run_time(extra_volume, flow_rate * 0.5).to_timedelta(),
                kwargs={"volume": extra_volume, "flow_rate": flow_rate * 0.5}
            ),
            Event(  # here to stop alarm on pump if it is sounded
                resource=pump,
                callable_=SyringePumpHarvard.write_stop,
                duration=timedelta(milliseconds=1),
            )
        ]
    )



def job_undo_fill_syringe(volume: Quantity, flow_rate: Quantity, valve: str, pump: str) -> JobSequence:
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


def job_fill_syringe_multiple(
        volume: Iterable[Quantity],
        flow_rate: Iterable[Quantity],
        valves: Iterable[str],
        pumps: Iterable[str],
) -> JobConcurrent:
    return JobConcurrent(
        [job_fill_syringe(vol, flow, val, p) for vol, flow, val, p in zip(volume, flow_rate, valves, pumps)],
    )


def job_undo_fill_syringe_multiple(
        volume: Iterable[Quantity],
        flow_rate: Iterable[Quantity],
        valves: Iterable[str],
        pumps: Iterable[str],
) -> JobConcurrent:
    return JobConcurrent(
        [job_undo_fill_syringe(vol, flow, val, p) for vol, flow, val, p in zip(volume, flow_rate, valves, pumps)],
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


def write_atir_background() -> JobSequence:
    return JobSequence(
        [
            Event(
                resource=NamesSensors.ATIR,
                callable_=ATIR.write_background,
                duration=timedelta(seconds=20),
            )],
        delay=timedelta(seconds=10)
    )


def write_atir_measure() -> JobSequence:
    return JobSequence(
        [
            Event(
                resource=NamesSensors.ATIR,
                callable_=ATIR.write_measure,
                duration=timedelta(seconds=20),
            )]
    )


def add_atir(job: JobSequence | JobConcurrent) -> JobSequence:
    return JobSequence(
        [
            Event(
                resource=NamesSensors.ATIR,
                callable_=ATIR.write_continuous_event_handler,
                duration=timedelta(milliseconds=100),
                kwargs={
                    "event_handler":
                        ContinuousEventHandlerRepeatingNoEndSaving(
                            callable_=ATIR.write_measure.__name__
                        )
                }
            ),
            job,
            Event(
                resource=NamesSensors.ATIR,
                callable_=ATIR.write_stop,
                duration=timedelta(milliseconds=100),
            )
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
            pumps=pumps,
            delay=timedelta(seconds=0.5)
        ),
    ])


def flow_background():
    return JobConcurrent(
        [
            job_flow_syringe_multiple(
                volume=[1 * Unit.ml],
                flow_rate=[0.3 * Unit("ml/min")],
                valves=[NamesValves.ONE],
                pumps=[NamesPump.ONE]
            ),
            write_atir_background(),
        ]
    )


def flow_nmr_test():
    """
                # job_fill_syringe_multiple(
            #     volume=[1 * Unit.ml],
            #     flow_rate=[1 * Unit("ml/min")],
            #     valves=[NamesValves.TWO],
            #     pumps=[NamesPump.TWO]
            # ),
            # job_flow_syringe_multiple(
            #     volume=[0.2 * Unit.ml],
            #     flow_rate=[0.2 * Unit("ml/min")],
            #     valves=[NamesValves.TWO],
            #     pumps=[NamesPump.TWO]
            # ),
            # flow_nmr_test(),
            # Event(
            #     resource=NamesPump.FIVE,
            #     callable_=SyringePumpHarvard.write_infuse,
            #     duration=SyringePumpHarvard.compute_run_time(0.263 * Unit.ml, 0.25 * Unit("ml/min")).to_timedelta(),
            #     kwargs={"volume": 0.263 * Unit.ml, "flow_rate": 0.25 * Unit("ml/min")}
            # ),

    """
    return JobConcurrent(
        [
            job_flow_syringe_multiple(
                volume=[0.065 * Unit.ml],
                flow_rate=[0.065 * Unit("ml/min")],
                valves=[NamesValves.TWO],
                pumps=[NamesPump.TWO]
            ),
            Event(
                resource=NamesSensors.NMR,
                callable_=NMR.write_measure.__name__,
                duration=timedelta(seconds=30),
                kwargs={"scans": NMR.SCANS.ONE, "move_vol": 0.25 * Unit.ml},
                delay=timedelta(seconds=10)
            ),
        ]
    )


def job_main() -> JobSequence:
    return JobSequence(
        [
            # job_fill_syringe_multiple(
            #     volume=[0.5 * Unit.ml],
            #     flow_rate=[1 * Unit("ml/min")],
            #     valves=[NamesValves.FOUR],
            #     pumps=[NamesPump.FOUR]
            # ),
            # Event(
            #     resource=NamesPump.ONE,
            #     callable_=SyringePumpHarvard.write_infuse,
            #     duration=SyringePumpHarvard.compute_run_time(.3 * Unit.ml, 1 * Unit("ml/min")).to_timedelta(),
            #     kwargs={"volume": .2 * Unit.ml, "flow_rate": 1 * Unit("ml/min")}
            # ),
            # job_fill_syringe_multiple(
            #     volume=[0.5 * Unit.ml],
            #     flow_rate=[1 * Unit("ml/min")],
            #     valves=[NamesValves.FOUR],
            #     pumps=[NamesPump.FOUR]
            # ),
            job_fill_syringe_multiple(
                volume=[2 * Unit.ml],
                flow_rate=[1 * Unit("ml/min")],
                valves=[NamesValves.FOUR],
                pumps=[NamesPump.FOUR]
            ),



            # Event(
            #     resource=NamesPump.ONE,
            #     callable_=SyringePumpHarvard.write_force,
            #     duration=timedelta(seconds=1.5),
            #     kwargs={"force": 30}
            # ),
            # Event(
            #     resource=NamesEquipment.BATH,
            #     callable_=PolyRecirculatingBath.write_set_point,
            #     duration=timedelta(seconds=1.5),
            #     kwargs={"temperature": 34.2}
            # ),
            # fill_and_push(
            #     volume=[2 * Unit.ml],
            #     flow_rate=[1 * Unit("ml/min")],
            #     valves=[NamesValves.VALVE_FRONT],
            #     pumps=[NamesPump.PUMP_FRONT]
            # ),


            # Event(
            #     resource=NamesPump.TWO,
            #     callable_=SyringePumpHarvard.write_withdraw,
            #     duration=SyringePumpHarvard.compute_run_time(0.6 * Unit.ml, 1 * Unit("ml/min")).to_timedelta(),
            #     kwargs={"volume": 0.6 * Unit.ml, "flow_rate": 1 * Unit("ml/min")}
            # ),
            # Event(
            #     resource=NamesPump.ONE,
            #     callable_=SyringePumpHarvard.write_infuse,
            #     duration=SyringePumpHarvard.compute_run_time(1 * Unit.ml, 2 * Unit("ml/min")).to_timedelta(),
            #     kwargs={"volume": 1 * Unit.ml, "flow_rate": 2 * Unit("ml/min")}
            # ),

            # write_atir_background(),
            # write_atir_measure(),
            # add_atir(
            #     job_flow_syringe_multiple(
            #         volume=[0.3 * Unit.ml],
            #         flow_rate=[0.3 * Unit("ml/min")],
            #         valves=[NamesValves.ONE],
            #         pumps=[NamesPump.ONE]
            #     )
            # ),

            # job_fill_syringe_multiple(
            #     volume=[6.5 * Unit.ml],
            #     flow_rate=[1 * Unit("ml/min")],
            #     valves=[NamesValves.THREE],
            #     pumps=[NamesPump.THREE],
            # ),
            # job_undo_fill_syringe_multiple(
            #     volume=[6 * Unit.ml],
            #     flow_rate=[2 * Unit("ml/min")],
            #     valves=[NamesValves.THREE],
            #     pumps=[NamesPump.THREE]
            # ),


            # job_fill_syringe_multiple(
            #     volume=[1 * Unit.ml, 1 * Unit.ml, 1 * Unit.ml],
            #     flow_rate=[1 * Unit("ml/min"), 1 * Unit("ml/min"),  1 * Unit("ml/min")],
            #     valves=[NamesValves.ONE, NamesValves.TWO,  NamesValves.FOUR],
            #     pumps=[NamesPump.ONE, NamesPump.TWO, NamesPump.FOUR]
            # ),
            # job_undo_fill_syringe_multiple(
            #     volume=[1 * Unit.ml, 1 * Unit.ml, 1 * Unit.ml],
            #     flow_rate=[1 * Unit("ml/min"), 1 * Unit("ml/min"), 1 * Unit("ml/min")],
            #     valves=[NamesValves.ONE, NamesValves.TWO, NamesValves.FOUR],
            #     pumps=[NamesPump.ONE, NamesPump.TWO, NamesPump.FOUR]
            # ),

            # job_flow_syringe_multiple(
            #     volume=[0.5 * Unit.ml, 0.5 * Unit.ml, 0.05 * Unit.ml, 0.05 * Unit.ml],
            #     flow_rate=[1 * Unit("ml/min"), 1 * Unit("ml/min"), 1 * Unit("ml/min"), 1 * Unit("ml/min")],
            #     valves=[NamesValves.ONE, NamesValves.TWO, NamesValves.THREE, NamesValves.FOUR],
            #     pumps=[NamesPump.ONE, NamesPump.TWO, NamesPump.THREE, NamesPump.FOUR],
            #     delay=timedelta(seconds=1)
            # ),

            # job_fill_syringe_multiple(
            #     volume=[1 * Unit.ml, 1 * Unit.ml],
            #     flow_rate=[1 * Unit("ml/min"), 1 * Unit("ml/min")],
            #     valves=[NamesValves.ONE, NamesValves.THREE],
            #     pumps=[NamesPump.ONE, NamesPump.THREE]
            # ),
            # job_flow_syringe_multiple(
            #     volume=[1 * Unit.ml, 1 * Unit.ml],
            #     flow_rate=[0.025 * Unit("ml/min"), 0.025 * Unit("ml/min")],
            #     valves=[NamesValves.ONE, NamesValves.THREE],
            #     pumps=[NamesPump.ONE, NamesPump.THREE]
            # ),




            # priming
            # Event(
            #     resource=NamesValves.FOUR,
            #     callable_=ValveServo.write_move,
            #     duration=timedelta(seconds=1.5),
            #     kwargs={"position": "flow"}
            # ),


            # main job


            # fill_and_push(
            #     volume=[1.5 * Unit.ml],
            #     flow_rate=[1 * Unit("ml/min")],
            #     valves=[NamesValves.TWO],
            #     pumps=[NamesPump.TWO]
            # ),
            # job_air_purge(),
            # job_air_purge(0.3 * Unit.mL),
        ]
    )


def main():
    job_submitter = JobSubmitter()
    result = job_submitter.submit(job_main())
    print(result)

    # full_schedule = job_submitter.get_schedule()
    # print(full_schedule)

    print("hi")


if __name__ == "__main__":
    main()
