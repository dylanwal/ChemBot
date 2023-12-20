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
                volume=[5.5 * Unit.ml, 1 * Unit.ml, 6.5 * Unit.ml, 1 * Unit.ml],
                flow_rate=[1 * Unit("ml/min"), 1 * Unit("ml/min"), 1 * Unit("ml/min"), 1 * Unit("ml/min")],
                valves=[NamesValves.ONE, NamesValves.TWO, NamesValves.THREE, NamesValves.FOUR],
                pumps=[NamesPump.ONE, NamesPump.TWO, NamesPump.THREE, NamesPump.FOUR]
            ),
        ]
    )


def steady_state1(base_flow_rate, split):
    n = 2.5
    m = 1
    return JobSequence(
        [
            # Event(
            #     resource=NamesLEDColors.GREEN,
            #     callable_=LightPico.write_stop,
            #     duration=timedelta(milliseconds=100),
            # ),
            # job_flow_syringe_multiple(
            #     volume=[
            #         reactor_volume * n / 2 * (1-split),
            #         reactor_volume * n / 2,
            #         reactor_volume * n / 2 * split,
            #     ],
            #     flow_rate=[
            #         base_flow_rate * (1-split),
            #         base_flow_rate,
            #         base_flow_rate * split,
            #     ],
            #     valves=[NamesValves.ONE, NamesValves.THREE, NamesValves.TWO],
            #     pumps=[NamesPump.ONE, NamesPump.THREE, NamesPump.TWO],
            # ),
            Event(
                resource=NamesLEDColors.GREEN,
                callable_=LightPico.write_power,
                duration=timedelta(milliseconds=100),
                kwargs={"power": int(65535 * light_power)},
            ),
            job_flow_syringe_multiple(
                volume=[
                    reactor_volume * m / 2 * (1-split),
                    reactor_volume * m / 2,
                    reactor_volume * m / 2 * split,
                ],
                flow_rate=[
                    base_flow_rate * (1-split),
                    base_flow_rate,
                    base_flow_rate * split,
                ],
                valves=[NamesValves.ONE, NamesValves.THREE, NamesValves.TWO],
                pumps=[NamesPump.ONE, NamesPump.THREE, NamesPump.TWO],
            ),
        ]
    )


def steady_state2(base_flow_rate, split):
    n = 3
    m = 4
    return JobSequence(
        [
            Event(
                resource=NamesLEDColors.GREEN,
                callable_=LightPico.write_power,
                duration=timedelta(milliseconds=100),
                kwargs={"power": int(65535 * light_power)},
            ),
            job_flow_syringe_multiple(
                volume=[
                    reactor_volume * n / 2 * (1-split),
                    reactor_volume * n / 2,
                    reactor_volume * n / 2 * split,
                ],
                flow_rate=[
                    base_flow_rate * (1-split),
                    base_flow_rate,
                    base_flow_rate * split,
                ],
                valves=[NamesValves.ONE, NamesValves.THREE, NamesValves.FOUR],
                pumps=[NamesPump.ONE, NamesPump.THREE, NamesPump.FOUR],
            ),
            Event(
                resource=NamesLEDColors.GREEN,
                callable_=LightPico.write_stop,
                duration=timedelta(milliseconds=100),
            ),
            job_flow_syringe_multiple(
                volume=[
                    reactor_volume * m / 2 * (1-split),
                    reactor_volume * m / 2,
                    reactor_volume * m / 2 * split,
                ],
                flow_rate=[
                    base_flow_rate * (1-split),
                    base_flow_rate,
                    base_flow_rate * split,
                ],
                valves=[NamesValves.ONE, NamesValves.THREE, NamesValves.FOUR],
                pumps=[NamesPump.ONE, NamesPump.THREE, NamesPump.FOUR],
            ),
        ]
    )


def main_flow(base_flow_rate, split) -> JobSequence:
    t_0 = 60 * 60
    n = int(t_0/10)
    t = np.linspace(0, t_0, n)

    mon_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], [base_flow_rate * (1-split)] * n, t)
    fl_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], [base_flow_rate] * n, t)

    def m1(t_):
        return (base_flow_rate * split) * (1 - t_/t_0)

    def m2(t_):
        return (base_flow_rate * split) * (t_/t_0)

    m1_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], [m1(t_) for t_ in t], t)

    m2_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], [m2(t_) for t_ in t], t)

    return JobSequence(
        [
            Event(
                resource=NamesLEDColors.GREEN,
                callable_=LightPico.write_power,
                duration=timedelta(milliseconds=100),
                kwargs={"power": int(65535 * light_power)},
            ),
            job_flow_syringe_multiple(
                volume=[
                    6 * Unit.ml,
                    3 * Unit.ml,
                    6 * Unit.ml,
                    3 * Unit.ml,
                ],
                flow_rate=[
                    base_flow_rate*(1-split),
                    base_flow_rate*split,
                    base_flow_rate,
                    base_flow_rate*split,
                ],
                valves=[NamesValves.ONE, NamesValves.TWO, NamesValves.THREE, NamesValves.FOUR],
                pumps=[NamesPump.ONE, NamesPump.TWO, NamesPump.THREE, NamesPump.FOUR],
                duration=False  # <<<<< will not block
            ),

            Event(
                resource=NamesPump.ONE,
                callable_=SyringePumpHarvard.write_continuous_event_handler,
                duration=timedelta(milliseconds=100),
                kwargs={"event_handler": mon_profile},
            ),
            Event(
                resource=NamesPump.TWO,
                callable_=SyringePumpHarvard.write_continuous_event_handler,
                duration=timedelta(milliseconds=100),
                kwargs={"event_handler": m1_profile},
            ),
            Event(
                resource=NamesPump.THREE,
                callable_=SyringePumpHarvard.write_continuous_event_handler,
                duration=timedelta(milliseconds=100),
                kwargs={"event_handler": fl_profile},
            ),
            Event(
                resource=NamesPump.FOUR,
                callable_=SyringePumpHarvard.write_continuous_event_handler,
                duration=timedelta(milliseconds=100),
                kwargs={"event_handler": m2_profile},
            ),


            Event(
                resource=NamesLEDColors.GREEN,
                callable_=LightPico.write_stop,
                duration=timedelta(milliseconds=100),
                delay=timedelta(seconds=t_0)
            ),

            # turn off pumps
            Event(
                resource=NamesPump.ONE,
                callable_=LightPico.write_stop,
                duration=timedelta(milliseconds=100),
            ),
            Event(
                resource=NamesPump.TWO,
                callable_=LightPico.write_stop,
                duration=timedelta(milliseconds=100),
            ),
            Event(
                resource=NamesPump.THREE,
                callable_=LightPico.write_stop,
                duration=timedelta(milliseconds=100),
            ),
            Event(
                resource=NamesPump.FOUR,
                callable_=LightPico.write_stop,
                duration=timedelta(milliseconds=100),
            ),
        ]
    )


def main_job() -> JobSequence:
    split = 1 - 0.31
    base_flow_rate = (0.03275 * Unit("ml/min"))

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

            steady_state1(base_flow_rate, split),
            main_flow(base_flow_rate, split),
            steady_state2(base_flow_rate, split),

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
