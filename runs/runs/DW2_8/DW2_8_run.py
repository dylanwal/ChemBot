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
                volume=[4 * Unit.ml, 0.5 * Unit.ml, 4 * Unit.ml, 0.5 * Unit.ml],
                flow_rate=[1 * Unit("ml/min"), 1 * Unit("ml/min"), 1 * Unit("ml/min"), 1 * Unit("ml/min")],
                valves=[NamesValves.ONE, NamesValves.TWO, NamesValves.THREE, NamesValves.FOUR],
                pumps=[NamesPump.ONE, NamesPump.TWO, NamesPump.THREE, NamesPump.FOUR]
            ),
        ]
    )


def main_flow() -> JobSequence:
    t_0 = (16 + 120 + 24 + 16) * 60
    n = int(t_0/10)

    base = 0.03275 * Unit("ml/min")
    t = np.linspace(0, t_0, n)

    mon_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], [base * 0.8] * n, t)
    fl_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], [base] * n, t)

    def cta_py(t_):
        if t_ < (16 * 60):
            return base * 0.2
        if t_ < ((16 + 120) * 60):
            t_ = t_ - (16 * 60)
            return (base * 0.2) * (1 - t_/(120*60+0.1))
        return 0.0001 * Unit("ml/min")

    cta_py_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], [cta_py(t_) for t_ in t], t)

    def cta_btpa(t_):
        if t_ < (16 * 60):
            return 0.0001 * Unit("ml/min")
        if t_ < ((16 + 120) * 60):
            t_ = t_ - (16 * 60)
            return (base * 0.2) * ((t_+0.1)/(120*60))
        return base * 0.2

    cta_btpa_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], [cta_btpa(t_) for t_ in t], t)

    return JobSequence(
        [
            job_flow_syringe_multiple(
                volume=[
                    6 * Unit.ml,
                    6 * Unit.ml,
                    6 * Unit.ml,
                    6 * Unit.ml,
                ],
                flow_rate=[
                    mon_profile.kwargs_values[0],
                    cta_py_profile.kwargs_values[0],
                    fl_profile.kwargs_values[0],
                    cta_btpa_profile.kwargs_values[0],
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
                kwargs={"event_handler": cta_py_profile},
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
                kwargs={"event_handler": cta_btpa_profile},
            ),

            Event(
                resource=NamesLEDColors.GREEN,
                callable_=LightPico.write_power,
                duration=timedelta(milliseconds=100),
                kwargs={"power": int(65535 * 0.5)},
                delay=timedelta(minutes=16)
            ),
            Event(
                resource=NamesLEDColors.GREEN,
                callable_=LightPico.write_stop,
                duration=timedelta(milliseconds=100),
                delay=timedelta(minutes=24+120)
            ),
            Event(
                resource=NamesLEDColors.GREEN,
                callable_=LightPico.write_stop,
                duration=timedelta(milliseconds=100),
                delay=timedelta(minutes=16)
            ),
        ]
    )


def main_flow2() -> JobSequence:
    base = 0.03275 * Unit("ml/min")
    return JobSequence([
        Event(
            resource=NamesLEDColors.GREEN,
            callable_=LightPico.write_power,
            duration=timedelta(milliseconds=100),
            kwargs={"power": int(65535 * 0.3)},
        ),
        job_flow_syringe_multiple(
            volume=[
                0.8 * Unit.ml,
                0.1 * Unit.ml,
                1 * Unit.ml,
                0.1 * Unit.ml,
            ],
            flow_rate=[
                base*0.8,
                base*0.1,
                base,
                base * 0.1,
            ],
            valves=[NamesValves.ONE, NamesValves.TWO, NamesValves.THREE, NamesValves.FOUR],
            pumps=[NamesPump.ONE, NamesPump.TWO, NamesPump.THREE, NamesPump.FOUR],
        ),
        Event(
            resource=NamesLEDColors.GREEN,
            callable_=LightPico.write_stop,
            duration=timedelta(milliseconds=100),
        ),
    ])


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
            Event(
                resource=NamesEquipment.BATH,
                callable_=PolyRecirculatingBath.write_stop,
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
