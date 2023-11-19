from datetime import timedelta
from typing import Iterable

from unitpy import Unit, Quantity
import numpy as np

from chembot.scheduler import JobSequence, JobConcurrent, Event
from chembot.scheduler.job_submitter import JobSubmitter
from chembot.equipment.valves import ValveServo
from chembot.equipment.pumps import SyringePumpHarvard
from chembot.equipment.sensors import ATIR, NMR
from chembot.equipment.lights import LightPico
from chembot.equipment.continuous_event_handler import ContinuousEventHandlerRepeatingNoEndSaving, \
    ContinuousEventHandlerProfile

from runs.launch_equipment.names import NamesPump, NamesValves, NamesSensors, NamesLEDColors


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
    extra_volume = 0.15 * Unit.ml
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
            Event(  # here to stop alarm on pump if it is sounded
                resource=pump,
                callable_=SyringePumpHarvard.write_stop,
                duration=timedelta(milliseconds=1),
                delay=timedelta(milliseconds=50)
            ),
            Event(
                resource=pump,
                callable_=SyringePumpHarvard.write_infuse,
                duration=SyringePumpHarvard.compute_run_time(extra_volume, 0.25 * Unit("ml/min")).to_timedelta(),
                kwargs={"volume": extra_volume, "flow_rate": 0.25 * Unit("ml/min")},
                delay=timedelta(seconds=1)
            ),
            Event(  # here to stop alarm on pump if it is sounded
                resource=pump,
                callable_=SyringePumpHarvard.write_stop,
                duration=timedelta(milliseconds=10),
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


def main_fill() -> JobSequence:
    return JobSequence(
        [
            job_fill_syringe_multiple(
                volume=[1 * Unit.ml, 1 * Unit.ml],
                flow_rate=[1 * Unit("ml/min"), 1 * Unit("ml/min")],
                valves=[NamesValves.ONE, NamesValves.THREE],
                pumps=[NamesPump.ONE, NamesPump.THREE]
            ),
        ]
    )


def main_flow() -> JobSequence:
    return JobSequence(
        [
            # # 8 min residence time, 5 % power
            # Event(
            #     resource=NamesLEDColors.GREEN,
            #     callable_=LightPico.write_power,
            #     duration=timedelta(milliseconds=100),
            #     kwargs={"power": int(65535 * 0.05)},
            # ),
            # job_flow_syringe_multiple(
            #     volume=[0.5 * Unit.ml, 0.5 * Unit.ml],
            #     flow_rate=[0.03275 * Unit("ml/min"), 0.03275 * Unit("ml/min")],
            #     valves=[NamesValves.ONE, NamesValves.ONE],
            #     pumps=[NamesPump.ONE, NamesPump.ONE]
            # ),
            # # 8 min residence time, 10 % power
            # Event(
            #     resource=NamesLEDColors.GREEN,
            #     callable_=LightPico.write_power,
            #     duration=timedelta(milliseconds=100),
            #     kwargs={"power": int(65535 * 0.1)},
            # ),
            # job_flow_syringe_multiple(
            #     volume=[0.5 * Unit.ml, 0.5 * Unit.ml],
            #     flow_rate=[0.03275 * Unit("ml/min"), 0.03275 * Unit("ml/min")],
            #     valves=[NamesValves.ONE, NamesValves.ONE],
            #     pumps=[NamesPump.ONE, NamesPump.ONE]
            # ),



            # 8 min residence time, 20 % power
            Event(
                resource=NamesLEDColors.GREEN,
                callable_=LightPico.write_power,
                duration=timedelta(milliseconds=100),
                kwargs={"power": int(65535 * 0.2)},
            ),
            job_flow_syringe_multiple(
                volume=[1 * Unit.ml, 1 * Unit.ml],
                flow_rate=[0.03275*2 * Unit("ml/min"), 0.03275*2 * Unit("ml/min")],
                valves=[NamesValves.ONE, NamesValves.THREE],
                pumps=[NamesPump.ONE, NamesPump.THREE]
            ),

            # job_flow_syringe_multiple(
            #     volume=[1 * Unit.ml],
            #     flow_rate=[0.065 * Unit("ml/min")],
            #     valves=[NamesValves.FOUR],
            #     pumps=[NamesPump.FOUR]
            # ),



            # 8 min residence time, 30 % power
            # Event(
            #     resource=NamesLEDColors.GREEN,
            #     callable_=LightPico.write_power,
            #     duration=timedelta(milliseconds=100),
            #     kwargs={"power": int(65535 * 0.3)},
            # ),
            # job_flow_syringe_multiple(
            #     volume=[0.5 * Unit.ml, 0.5 * Unit.ml],
            #     flow_rate=[0.03275 * Unit("ml/min"), 0.03275 * Unit("ml/min")],
            #     valves=[NamesValves.ONE, NamesValves.ONE],
            #     pumps=[NamesPump.ONE, NamesPump.ONE]
            # )
            Event(
                resource=NamesLEDColors.GREEN,
                callable_=LightPico.write_stop,
                duration=timedelta(milliseconds=100),
            ),
        ]
    )


def main_job() -> JobSequence:
    return JobSequence(
        [
            main_fill(),
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
                            callable_=NMR.write_measure.__name__
                        )
                }
            ),

            main_flow(),

            Event(
                resource=NamesSensors.ATIR,
                callable_=ATIR.write_stop,
                duration=timedelta(milliseconds=100),
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
    job = main_job()
    result = job_submitter.submit(job)
    print(result)

    # full_schedule = job_submitter.get_schedule()
    # print(full_schedule)

    print("hi")


if __name__ == "__main__":
    main()
