from datetime import timedelta
from typing import Iterable

from unitpy import Unit, Quantity
import numpy as np

from chembot.scheduler import JobSequence, JobConcurrent, Event
from chembot.scheduler.job_submitter import JobSubmitter
from chembot.equipment.valves import ValveServo
from chembot.equipment.pumps import SyringePumpHarvard
from chembot.equipment.sensors import PhaseSensor, ATIR, NMR
from chembot.equipment.lights import LightPico
from chembot.equipment.continuous_event_handler import ContinuousEventHandlerRepeatingNoEndSaving, \
    ContinuousEventHandlerProfile

from runs.launch_equipment.names import NamesPump, NamesValves, NamesSensors, NamesLEDColors


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


def write_atir_background() -> JobSequence:
    return JobSequence(
        [
            Event(
                resource=NamesSensors.ATIR,
                callable_=ATIR.write_background,
                duration=timedelta(seconds=20),
            )]
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
            )]
    )


def add_linear_light(
        job,
        n: int = 100,
        duration: timedelta = timedelta(seconds=10),
        led_name: str = NamesLEDColors.GREEN,
        power_min: int = 0,
        power_max: int = 65535
):
    # power is [0, 65535]
    lin_space = np.linspace(power_min, power_max, n, dtype=np.uint32)
    time_delta_array = np.linspace(0, duration.total_seconds(), n)
    profile = ContinuousEventHandlerProfile(LightPico.write_power, ["power"], lin_space, time_delta_array)
    return JobSequence(
        [
            Event(
                resource=led_name,
                callable_=LightPico.write_continuous_event_handler,
                duration=timedelta(milliseconds=100),
                kwargs={"event_handler": profile},
            ),
            job,
            Event(led_name, LightPico.write_stop, timedelta(microseconds=100))

        ],
        name="linear_sweep"
    )


def job_air_purge(volume: Quantity = 1 * Unit.ml, flow_rate: Quantity = 5 * Unit("ml/min")) -> JobSequence:
    return JobSequence(
        [
            job_fill_syringe(volume, flow_rate, NamesValves.BACK, NamesPump.BACK),
            Event(
                resource=NamesValves.FRONT,
                callable_=ValveServo.write_move,
                duration=timedelta(seconds=1.5),
                kwargs={"position": "fill"}
            ),
            Event(
                resource=NamesValves.MIDDLE,
                callable_=ValveServo.write_move,
                duration=timedelta(seconds=1.5),
                kwargs={"position": "flow_air"}
            ),
            job_flow(volume, flow_rate, NamesValves.BACK, NamesPump.BACK)
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
            job_fill_syringe_multiple(
                volume=[5 * Unit.ml, 5 * Unit.ml],
                flow_rate=[1.5 * Unit("ml/min"), 1.5 * Unit("ml/min")],
                valves=[NamesValves.THREE, NamesValves.FOUR],
                pumps=[NamesPump.THREE, NamesPump.FOUR]
            ),

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
            Event(
                resource=NamesSensors.NMR,
                callable_=NMR.write_continuous_event_handler,
                duration=timedelta(milliseconds=100),
                kwargs={
                    "event_handler":
                        ContinuousEventHandlerRepeatingNoEndSaving(
                            callable_=ATIR.write_measure.__name__
                        )
                }
            ),

            # prime (8 min)
            job_flow_syringe_multiple(
                volume=[1 * Unit.ml, 1 * Unit.ml],
                flow_rate=[0.0328 * Unit("ml/min"), 0.0328 * Unit("ml/min")],
                valves=[NamesValves.FOUR, NamesValves.THREE],
                pumps=[NamesPump.FOUR, NamesPump.THREE]
            ),

            # 2 min residence time
            job_flow_syringe_multiple(
                volume=[0.5 * Unit.ml, 0.5 * Unit.ml],
                flow_rate=[0.13 * Unit("ml/min"), 0.13 * Unit("ml/min")],
                valves=[NamesValves.FOUR, NamesValves.THREE],
                pumps=[NamesPump.FOUR, NamesPump.THREE]
            ),
            # 4 min residence time
            job_flow_syringe_multiple(
                volume=[0.5 * Unit.ml, 0.5 * Unit.ml],
                flow_rate=[0.065 * Unit("ml/min"), 0.065 * Unit("ml/min")],
                valves=[NamesValves.FOUR, NamesValves.THREE],
                pumps=[NamesPump.FOUR, NamesPump.THREE]
            ),
            # 8 min residence time
            job_flow_syringe_multiple(
                volume=[0.5 * Unit.ml, 0.5 * Unit.ml],
                flow_rate=[0.0328 * Unit("ml/min"), 0.0328 * Unit("ml/min")],
                valves=[NamesValves.FOUR, NamesValves.THREE],
                pumps=[NamesPump.FOUR, NamesPump.THREE]
            ),
            # 16 min residence time
            job_flow_syringe_multiple(
                volume=[0.5 * Unit.ml, 0.5 * Unit.ml],
                flow_rate=[0.0164 * Unit("ml/min"), 0.0164 * Unit("ml/min")],
                valves=[NamesValves.FOUR, NamesValves.THREE],
                pumps=[NamesPump.FOUR, NamesPump.THREE]
            ),
            # 32 min residence time
            job_flow_syringe_multiple(
                volume=[0.5 * Unit.ml, 0.5 * Unit.ml],
                flow_rate=[0.0082 * Unit("ml/min"), 0.0082 * Unit("ml/min")],
                valves=[NamesValves.FOUR, NamesValves.THREE],
                pumps=[NamesPump.FOUR, NamesPump.THREE]
            ),

            # stop
            job_flow_syringe_multiple(
                volume=[0.1 * Unit.ml, 0.1 * Unit.ml],
                flow_rate=[0.2 * Unit("ml/min"), 0.2 * Unit("ml/min")],
                valves=[NamesValves.FOUR, NamesValves.THREE],
                pumps=[NamesPump.FOUR, NamesPump.THREE],
                delay=timedelta(minutes=2)
            ),
            job_flow_syringe_multiple(
                volume=[0.1 * Unit.ml, 0.1 * Unit.ml],
                flow_rate=[0.2 * Unit("ml/min"), 0.2 * Unit("ml/min")],
                valves=[NamesValves.FOUR, NamesValves.THREE],
                pumps=[NamesPump.FOUR, NamesPump.THREE],
                delay=timedelta(minutes=2)
            ),
            job_flow_syringe_multiple(
                volume=[0.1 * Unit.ml, 0.1 * Unit.ml],
                flow_rate=[0.2 * Unit("ml/min"), 0.2 * Unit("ml/min")],
                valves=[NamesValves.FOUR, NamesValves.THREE],
                pumps=[NamesPump.FOUR, NamesPump.THREE],
                delay=timedelta(minutes=2)
            ),
            job_flow_syringe_multiple(
                volume=[0.1 * Unit.ml, 0.1 * Unit.ml],
                flow_rate=[0.2 * Unit("ml/min"), 0.2 * Unit("ml/min")],
                valves=[NamesValves.FOUR, NamesValves.THREE],
                pumps=[NamesPump.FOUR, NamesPump.THREE],
                delay=timedelta(minutes=2)
            ),
            job_flow_syringe_multiple(
                volume=[0.1 * Unit.ml, 0.1 * Unit.ml],
                flow_rate=[0.2 * Unit("ml/min"), 0.2 * Unit("ml/min")],
                valves=[NamesValves.FOUR, NamesValves.THREE],
                pumps=[NamesPump.FOUR, NamesPump.THREE],
                delay=timedelta(minutes=2)
            ),

            # end
            Event(
                resource=NamesSensors.ATIR,
                callable_=ATIR.write_stop,
                duration=timedelta(milliseconds=100),
                delay=timedelta(minutes=5)
            ),
            Event(
                resource=NamesSensors.NMR,
                callable_=NMR.write_stop,
                duration=timedelta(milliseconds=100),
            ),
        ]
    )


def main():
    job_submitter = JobSubmitter()
    job = job_droplets()
    result = job_submitter.submit(job)
    print(result)

    # full_schedule = job_submitter.get_schedule()
    # print(full_schedule)

    print("hi")


if __name__ == "__main__":
    main()