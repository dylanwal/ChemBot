from __future__ import annotations
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


class DynamicProfile:
    def __init__(self, profile: np.ndarray):
        self.profile = profile

    @property
    def time(self) -> np.ndarray:
        return self.profile[:, 0] * 60  # min to sec conversion

    @property
    def temp(self) -> np.ndarray:
        return self.profile[:, 1]

    @property
    def light(self):
        return self.profile[:, 2]

    @property
    def flow_rate_mon(self):
        return self.profile[:, 3]

    @property
    def flow_rate_ctabtpa(self):
        return self.profile[:, 4]

    @property
    def flow_rate_ctapy(self):
        return self.profile[:, 5]

    @property
    def flow_rate_fl(self):
        return self.profile[:, 6]

    @staticmethod
    def get_volume(t: np.ndarray, flow_rate: np.ndarray):
        return np.trapz(x=t, y=flow_rate)

    @classmethod
    def load_profiles(cls, path: str) -> DynamicProfile:
        # t, temp, light, flow_rate_mon, flow_rate_cat, flow_rate_dmso
        data = np.loadtxt(path, delimiter=",")
        return DynamicProfile(data)


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


def steady_state(profile: DynamicProfile):
    mon_vol = float(profile.flow_rate_mon[0]) * Unit("ml") * 21  # (3*7min) * flowrate(ml/min) = ml|7min residence time
    cat_vol = float(profile.flow_rate_ctabtpa[0]) * Unit("ml") * 21
    fl_vol = float(profile.flow_rate_fl[0]) * Unit("ml") * 21
    dmso_vol = float(profile.flow_rate_ctapy[0]) * Unit("ml") * 21

    return JobSequence(
        [
            Event(
                resource=NamesEquipment.BATH,
                callable_=PolyRecirculatingBath.write_set_point,
                duration=timedelta(milliseconds=100),
                kwargs={"temperature": float(profile.temp[0])},
            ),

            job_fill_syringe_multiple(
                volume=[
                    mon_vol,
                    fl_vol,
                ],
                flow_rate=[
                    1 * Unit("ml/min"),
                    1 * Unit("ml/min"),
                ],
                valves=[NamesValves.ONE, NamesValves.THREE],
                pumps=[NamesPump.ONE, NamesPump.THREE]
            ),
            Event(
                resource=NamesLEDColors.GREEN,
                callable_=LightPico.write_power,
                duration=timedelta(milliseconds=100),
                kwargs={"power": int(profile.light[0] * 65535)},
            ),

            job_flow_syringe_multiple(
                volume=[
                    mon_vol,
                    cat_vol,
                    fl_vol,
                    dmso_vol,
                ],
                flow_rate=[
                    float(profile.flow_rate_mon[0]) * Unit("ml/min"),
                    float(profile.flow_rate_ctabtpa[0]) * Unit("ml/min"),
                    float(profile.flow_rate_fl[0]) * Unit("ml/min"),
                    float(profile.flow_rate_ctapy[0]) * Unit("ml/min"),
                ],
                valves=[NamesValves.ONE, NamesValves.TWO, NamesValves.THREE, NamesValves.FOUR],
                pumps=[NamesPump.ONE, NamesPump.TWO, NamesPump.THREE, NamesPump.FOUR]
            ),

            # stop
            Event(
                resource=NamesLEDColors.GREEN,
                callable_=LightPico.write_stop,
                duration=timedelta(milliseconds=100),
            ),
        ]
    )


def steady_state2(profile: DynamicProfile):
    mon_vol = float(profile.flow_rate_mon[0]) * Unit("ml") * 7  # (3*7min) * flowrate(ml/min) = ml|7min residence time
    cat_vol = float(profile.flow_rate_ctabtpa[0]) * Unit("ml") * 7
    fl_vol = float(profile.flow_rate_fl[0]) * Unit("ml") * 7
    dmso_vol = float(profile.flow_rate_ctapy[0]) * Unit("ml") * 7

    return JobSequence(
        [
            Event(
                resource=NamesEquipment.BATH,
                callable_=PolyRecirculatingBath.write_set_point,
                duration=timedelta(milliseconds=100),
                kwargs={"temperature": float(profile.temp[0])},
            ),

            # job_fill_syringe_multiple(
            #     volume=[
            #         mon_vol,
            #         fl_vol,
            #     ],
            #     flow_rate=[
            #         1 * Unit("ml/min"),
            #         1 * Unit("ml/min"),
            #     ],
            #     valves=[NamesValves.ONE, NamesValves.THREE],
            #     pumps=[NamesPump.ONE, NamesPump.THREE]
            # ),
            Event(
                resource=NamesLEDColors.GREEN,
                callable_=LightPico.write_power,
                duration=timedelta(milliseconds=100),
                kwargs={"power": int(profile.light[0] * 65535)},
            ),

            job_flow_syringe_multiple(
                volume=[
                    mon_vol,
                    cat_vol,
                    fl_vol,
                    dmso_vol,
                ],
                flow_rate=[
                    float(profile.flow_rate_mon[0]) * Unit("ml/min"),
                    float(profile.flow_rate_ctabtpa[0]) * Unit("ml/min"),
                    float(profile.flow_rate_fl[0]) * Unit("ml/min"),
                    float(profile.flow_rate_ctapy[0]) * Unit("ml/min"),
                ],
                valves=[NamesValves.ONE, NamesValves.TWO, NamesValves.THREE, NamesValves.FOUR],
                pumps=[NamesPump.ONE, NamesPump.TWO, NamesPump.THREE, NamesPump.FOUR]
            ),

            # stop
            Event(
                resource=NamesLEDColors.GREEN,
                callable_=LightPico.write_stop,
                duration=timedelta(milliseconds=100),
            ),
        ]
    )

def job_segment(profile: DynamicProfile, start: int, end: int):
    t = profile.time[start:end]
    t = t - t[0]

    temp = profile.temp[start: end]
    light = profile.light[start: end]
    flow_rate_mon = profile.flow_rate_mon[start: end]
    flow_rate_ctabtpa = profile.flow_rate_ctabtpa[start: end]
    flow_rate_ctapy = profile.flow_rate_ctapy[start: end]
    flow_rate_fl = profile.flow_rate_fl[start:end]

    mon_vol = profile.get_volume(t/60, flow_rate_mon) * Unit("ml")
    ctabtpa_vol = profile.get_volume(t/60, flow_rate_ctabtpa) * Unit("ml")
    fl_vol = profile.get_volume(t/60, flow_rate_fl) * Unit("ml")
    ctapy_vol = profile.get_volume(t/60, flow_rate_ctapy) * Unit("ml")

    # power is [0, 65535]
    light_profile = ContinuousEventHandlerProfile(LightPico.write_power, ["power"], (light * 65535).astype(np.int32), t)
    temp_profile = ContinuousEventHandlerProfile(PolyRecirculatingBath.write_set_point, ["temperature"], temp, t)
    _flow_rate_mon = tuple(f * Unit("ml/min") for f in flow_rate_mon)
    mon_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], _flow_rate_mon, t)
    _flow_rate_ctabtpa = tuple(f * Unit("ml/min") for f in flow_rate_ctabtpa)
    ctabtpa_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], _flow_rate_ctabtpa, t)
    _flow_rate_ctapy = tuple(f * Unit("ml/min") for f in flow_rate_ctapy)
    ctapy_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], _flow_rate_ctapy, t)
    _fl_flow_rate = tuple(f * Unit("ml/min") for f in flow_rate_fl)
    fl_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], _fl_flow_rate, t)

    return JobSequence(
        [
            job_fill_syringe_multiple(
                volume=[
                    mon_vol,
                    fl_vol,
                ],
                flow_rate=[
                    1 * Unit("ml/min"),
                    1 * Unit("ml/min"),
                ],
                valves=[NamesValves.ONE, NamesValves.THREE],
                pumps=[NamesPump.ONE, NamesPump.THREE]
            ),

            job_flow_syringe_multiple(
                volume=[
                    mon_vol * 2,
                    ctabtpa_vol * 2,
                    fl_vol * 2,
                    ctapy_vol * 2,
                ],
                flow_rate=[
                    float(flow_rate_mon[0]) * Unit("ml/min"),
                    float(flow_rate_ctabtpa[0]) * Unit("ml/min"),
                    float(flow_rate_fl[0]) * Unit("ml/min"),
                    float(flow_rate_ctapy[0]) * Unit("ml/min"),
                ],
                valves=[NamesValves.ONE, NamesValves.TWO, NamesValves.THREE, NamesValves.FOUR],
                pumps=[NamesPump.ONE, NamesPump.TWO, NamesPump.THREE, NamesPump.FOUR],
                duration=False  # <<<<< will not block
            ),

            JobConcurrent(
                [
                    Event(
                        resource=NamesLEDColors.GREEN,
                        callable_=LightPico.write_continuous_event_handler,
                        duration=timedelta(milliseconds=100),
                        kwargs={"event_handler": light_profile},
                    ),
                    Event(
                        resource=NamesEquipment.BATH,
                        callable_=PolyRecirculatingBath.write_continuous_event_handler,
                        duration=timedelta(milliseconds=100),
                        kwargs={"event_handler": temp_profile},
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
                        kwargs={"event_handler": ctabtpa_profile},
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
                        kwargs={"event_handler": ctapy_profile},
                    ),
                ],
                delay=timedelta(seconds=1)
            ),

            # stop
            JobConcurrent(
                [
                    Event(
                        resource=NamesLEDColors.GREEN,
                        callable_=LightPico.write_stop,
                        duration=timedelta(milliseconds=100),
                    ),
                    Event(
                        resource=NamesEquipment.BATH,
                        callable_=PolyRecirculatingBath.write_set_point,
                        duration=timedelta(milliseconds=100),
                        kwargs={"temperature": float(temp[-1])},
                    ),
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
                ],
                delay=timedelta(seconds=t[-1])
            )
        ]
    )


def job_main() -> JobSequence:
    profiles = DynamicProfile.load_profiles(r"DW2_10_profiles.csv")
    index_refill = [600, 1200, 1949]  # [100.03755163 200.07510327 324.95531356] * min

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
            steady_state2(profiles),
            job_segment(profiles, start=0, end=index_refill[0]),
            job_segment(profiles, start=index_refill[0], end=index_refill[1]),
            job_segment(profiles, start=index_refill[1], end=index_refill[2]),
            job_segment(profiles, start=index_refill[2], end=-1),
            steady_state(profiles),


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
                callable_=NMR.write_stop,
                duration=timedelta(milliseconds=100),
            ),
        ]
    )


def main():
    job_submitter = JobSubmitter()
    job = job_main()
    result = job_submitter.submit(job)
    print(result)

    # full_schedule = job_submitter.get_schedule()
    # print(full_schedule)

    print("hi")


if __name__ == "__main__":
    main()
