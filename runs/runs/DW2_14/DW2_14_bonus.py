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
from chembot.equipment.temperature_control import PolyRecirculatingBath
from chembot.equipment.continuous_event_handler import ContinuousEventHandlerRepeatingNoEndSaving, \
    ContinuousEventHandlerProfile

from runs.launch_equipment.names import NamesPump, NamesValves, NamesSensors, NamesLEDColors, NamesEquipment


reactor_volume = 0.525 * Unit.ml
light_power = 0.5

# def job_flow(volume: Quantity, flow_rate: Quantity, valve: str, pump: str) -> JobSequence:
#     flow_time = SyringePumpHarvard.compute_run_time(volume, flow_rate).to_timedelta()
#     force_delay = timedelta(seconds=30)
#     flow_time = flow_time - force_delay
#     return JobSequence(
#         [
#             Event(
#                 resource=valve,
#                 callable_=ValveServo.write_move,
#                 duration=timedelta(seconds=1.5),
#                 kwargs={"position": "flow"}
#             ),
#             Event(
#                 resource=pump,
#                 callable_=SyringePumpHarvard.write_infuse,
#                 duration=timedelta(seconds=0.1),
#                 kwargs={"volume": volume, "flow_rate": flow_rate}
#             ),
#             Event(
#                 resource=pump,
#                 callable_=SyringePumpHarvard.write_force,
#                 duration=timedelta(seconds=0.1),
#                 kwargs={"force": 40},
#                 delay=force_delay
#             ),
#             Event(  # here to stop alarm on pump if it is sounded
#                 resource=pump,
#                 callable_=SyringePumpHarvard.write_stop,
#                 duration=timedelta(milliseconds=1),
#                 delay=flow_time
#             )
#         ]
#     )


def job_flow(volume: Quantity, flow_rate: Quantity, valve: str, pump: str, duration: bool = True) -> JobSequence:
    job = JobSequence(
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
    if not duration:
        job = JobSequence(
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
                    duration=timedelta(milliseconds=100),
                    kwargs={"volume": volume, "flow_rate": flow_rate}
                )
            ]
        )

    return job


def job_fill_syringe(volume: Quantity, flow_rate: Quantity, valve: str, pump: str) -> JobSequence:
    extra_volume = 0.4 * Unit.ml
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
                duration=SyringePumpHarvard.compute_run_time(extra_volume, 0.3 * Unit("ml/min")).to_timedelta(),
                kwargs={"volume": extra_volume, "flow_rate": 0.3 * Unit("ml/min")},
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
        delay: timedelta = None,
        duration: bool = True
) -> JobConcurrent:
    return JobConcurrent(
        [job_flow(vol, flow, val, p, duration) for vol, flow, val, p in zip(volume, flow_rate, valves, pumps)],
        delay=delay  # to allow syringes to stabilize
    )


def main_fill() -> JobSequence:
    return JobSequence(
        [
            job_fill_syringe_multiple(
                volume=[2.5 * Unit.ml, 2.5 * Unit.ml],
                flow_rate=[1 * Unit("ml/min"), 1 * Unit("ml/min")],
                valves=[NamesValves.ONE, NamesValves.THREE],
                pumps=[NamesPump.ONE, NamesPump.THREE]
            ),
        ]
    )


def main_job() -> JobSequence:
    n = 2
    m = 6
    base_flow_rate = (0.03275 * Unit("ml/min"))  # 16 min res time

    return JobSequence(
        [
            # main_fill(),
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

            Event(
                resource=NamesLEDColors.GREEN,
                callable_=LightPico.write_power,
                duration=timedelta(milliseconds=100),
                kwargs={"power": int(65535 * 0.2)},
            ),

            # job_flow_syringe_multiple(
            #     volume=[
            #         reactor_volume * 3/2 * 0.575,
            #         reactor_volume * 3/2 * 0.185,
            #         reactor_volume * 3/2,
            #         reactor_volume * 3/2 * 0.240,
            #     ],
            #     flow_rate=[
            #         base_flow_rate*0.575,
            #         base_flow_rate*0.185,
            #         base_flow_rate,
            #         base_flow_rate*0.240,
            #     ],
            #     valves=[NamesValves.ONE, NamesValves.TWO, NamesValves.THREE, NamesValves.FOUR],
            #     pumps=[NamesPump.ONE, NamesPump.TWO, NamesPump.THREE, NamesPump.FOUR]
            # ),
            #
            # job_flow_syringe_multiple(
            #     volume=[
            #         reactor_volume * 3/2 * 0.575,
            #         reactor_volume * 3/2 * 0.369,
            #         reactor_volume * 3/2,
            #         reactor_volume * 3/2 * 0.055,
            #     ],
            #     flow_rate=[
            #         base_flow_rate * 0.575,
            #         base_flow_rate * 0.369,
            #         base_flow_rate,
            #         base_flow_rate * 0.055,
            #     ],
            #     valves=[NamesValves.ONE, NamesValves.TWO, NamesValves.THREE, NamesValves.FOUR],
            #     pumps=[NamesPump.ONE, NamesPump.TWO, NamesPump.THREE, NamesPump.FOUR]
            # ),
            job_flow_syringe_multiple(
                volume=[
                    reactor_volume * 3 * 0.575,
                    reactor_volume * 3 * 0.369,
                    reactor_volume * 3 * 0.055,
                ],
                flow_rate=[
                    base_flow_rate *2* 0.575,
                    base_flow_rate *2* 0.369,
                    base_flow_rate *2* 0.055,
                ],
                valves=[NamesValves.ONE, NamesValves.TWO, NamesValves.FOUR],
                pumps=[NamesPump.ONE, NamesPump.TWO, NamesPump.FOUR]
            ),
            job_flow_syringe_multiple(
                volume=[
                    reactor_volume * 3 * 0.575,
                    reactor_volume * 3 * 0.0925,
                    reactor_volume * 3 * 0.3325,
                ],
                flow_rate=[
                    base_flow_rate * 2 * 0.575,
                    base_flow_rate * 2 * 0.0925,
                    base_flow_rate * 2 * 0.3325,
                ],
                valves=[NamesValves.ONE, NamesValves.TWO, NamesValves.FOUR],
                pumps=[NamesPump.ONE, NamesPump.TWO, NamesPump.FOUR]
            ),

            Event(
                resource=NamesLEDColors.GREEN,
                callable_=LightPico.write_stop,
                duration=timedelta(milliseconds=100),
            ),
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
