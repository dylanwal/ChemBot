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
    def flow_rate_mon1(self):
        return self.profile[:, 3]

    @property
    def flow_rate_mon2(self):
        return self.profile[:, 4]

    @property
    def flow_rate_fl(self):
        return self.profile[:, 5]

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
    extra_volume = 0.5 * Unit.ml
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
    mon1_vol = float(profile.flow_rate_mon1[0]) * Unit("ml") * 5*7 # (3*7min) * flowrate(ml/min) = ml|7min residence time
    mon2_vol = float(profile.flow_rate_mon2[0]) * Unit("ml") * 5*7
    fl_vol = float(profile.flow_rate_fl[0]) * Unit("ml") * 5*7

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
                    mon1_vol,
                    mon2_vol,
                    fl_vol,
                ],
                flow_rate=[
                    1 * Unit("ml/min"),
                    1 * Unit("ml/min"),
                    0.8 * Unit("ml/min"),
                ],
                valves=[NamesValves.ONE, NamesValves.TWO, NamesValves.THREE],
                pumps=[NamesPump.ONE, NamesPump.TWO, NamesPump.THREE]
            ),

            Event(
                resource=NamesLEDColors.GREEN,
                callable_=LightPico.write_power,
                duration=timedelta(milliseconds=100),
                kwargs={"power": int(profile.light[0] * 65535)},
            ),

            job_flow_syringe_multiple(
                volume=[
                    mon1_vol,
                    mon2_vol,
                    fl_vol,
                ],
                flow_rate=[
                    float(profile.flow_rate_mon1[0]) * Unit("ml/min"),
                    float(profile.flow_rate_mon2[0]) * Unit("ml/min"),
                    float(profile.flow_rate_fl[0]) * Unit("ml/min"),
                ],
                valves=[NamesValves.ONE, NamesValves.TWO, NamesValves.THREE],
                pumps=[NamesPump.ONE, NamesPump.TWO, NamesPump.THREE]
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
    flow_rate_mon1 = profile.flow_rate_mon1[start: end]
    flow_rate_mon2 = profile.flow_rate_mon2[start: end]
    flow_rate_fl = profile.flow_rate_fl[start:end]

    mon1_vol = profile.get_volume(t/60, flow_rate_mon1) * Unit("ml")
    mon2_vol = profile.get_volume(t/60, flow_rate_mon2) * Unit("ml")
    fl_vol = profile.get_volume(t/60, flow_rate_fl) * Unit("ml")

    # power is [0, 65535]
    light_profile = ContinuousEventHandlerProfile(LightPico.write_power, ["power"], (light * 65535).astype(np.int32), t)
    temp_profile = ContinuousEventHandlerProfile(PolyRecirculatingBath.write_set_point, ["temperature"], temp, t)
    _flow_rate_mon = tuple(f * Unit("ml/min") for f in flow_rate_mon1)
    mon_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], _flow_rate_mon, t)
    _flow_rate_mon2 = tuple(f * Unit("ml/min") for f in flow_rate_mon2)
    mon2_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], _flow_rate_mon2, t)
    _fl_flow_rate = tuple(f * Unit("ml/min") for f in flow_rate_fl)
    fl_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], _fl_flow_rate, t)

    return JobSequence(
        [
            job_fill_syringe_multiple(
                volume=[
                    mon1_vol,
                    mon2_vol,
                    fl_vol,
                ],
                flow_rate=[
                    1 * Unit("ml/min"),
                    1 * Unit("ml/min"),
                    0.8 * Unit("ml/min"),
                ],
                valves=[NamesValves.ONE, NamesValves.TWO, NamesValves.THREE],
                pumps=[NamesPump.ONE, NamesPump.TWO, NamesPump.THREE]
            ),

            job_flow_syringe_multiple(
                volume=[
                    mon1_vol * 2,
                    mon2_vol * 2,
                    fl_vol * 2
                ],
                flow_rate=[
                    float(flow_rate_mon1[0]) * Unit("ml/min"),
                    float(flow_rate_mon2[0]) * Unit("ml/min"),
                    float(flow_rate_fl[0]) * Unit("ml/min"),
                ],
                valves=[NamesValves.ONE, NamesValves.TWO, NamesValves.THREE],
                pumps=[NamesPump.ONE, NamesPump.TWO, NamesPump.THREE],
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
                        kwargs={"event_handler": mon2_profile},
                    ),
                    Event(
                        resource=NamesPump.THREE,
                        callable_=SyringePumpHarvard.write_continuous_event_handler,
                        duration=timedelta(milliseconds=100),
                        kwargs={"event_handler": fl_profile},
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
                ],
                delay=timedelta(seconds=t[-1])
            )
        ]
    )


def job_segment2(profile: DynamicProfile, start: int, end: int):
    t = profile.time[start:end]
    t = t - t[0]

    temp = profile.temp[start: end]
    light = profile.light[start: end]
    flow_rate_mon1 = profile.flow_rate_mon1[start: end]
    flow_rate_mon2 = profile.flow_rate_mon2[start: end]
    flow_rate_fl = profile.flow_rate_fl[start:end]

    mon1_vol = profile.get_volume(t/60, flow_rate_mon1) * Unit("ml")
    mon2_vol = profile.get_volume(t/60, flow_rate_mon2) * Unit("ml")
    fl_vol = profile.get_volume(t/60, flow_rate_fl) * Unit("ml")

    # power is [0, 65535]
    light_profile = ContinuousEventHandlerProfile(LightPico.write_power, ["power"], (light * 65535).astype(np.int32), t)
    temp_profile = ContinuousEventHandlerProfile(PolyRecirculatingBath.write_set_point, ["temperature"], temp, t)
    _flow_rate_mon = tuple(f * Unit("ml/min") for f in flow_rate_mon1)
    mon_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], _flow_rate_mon, t)
    _flow_rate_mon2 = tuple(f * Unit("ml/min") for f in flow_rate_mon2)
    mon2_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], _flow_rate_mon2, t)
    _fl_flow_rate = tuple(f * Unit("ml/min") for f in flow_rate_fl)
    fl_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], _fl_flow_rate, t)

    return JobSequence(
        [
            job_flow_syringe_multiple(
                volume=[
                    mon1_vol * 2,
                    mon2_vol * 2,
                    fl_vol * 2
                ],
                flow_rate=[
                    float(flow_rate_mon1[0]) * Unit("ml/min"),
                    float(flow_rate_mon2[0]) * Unit("ml/min"),
                    float(flow_rate_fl[0]) * Unit("ml/min"),
                ],
                valves=[NamesValves.ONE, NamesValves.TWO, NamesValves.THREE],
                pumps=[NamesPump.ONE, NamesPump.TWO, NamesPump.THREE],
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
                        kwargs={"event_handler": mon2_profile},
                    ),
                    Event(
                        resource=NamesPump.THREE,
                        callable_=SyringePumpHarvard.write_continuous_event_handler,
                        duration=timedelta(milliseconds=100),
                        kwargs={"event_handler": fl_profile},
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
                ],
                delay=timedelta(seconds=t[-1])
            )
        ]
    )

def job_main() -> JobSequence:
    profiles = DynamicProfile.load_profiles(r"DW2_15_profiles.csv")
    index_refill = [660, 1320, 1979]  # [110.0413068  220.08261359 329.95719114] * min

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

            steady_state(profiles),
            # job_segment(profiles, start=0, end=index_refill[0]),
            # job_segment(profiles, start=index_refill[0], end=index_refill[1]),
            # job_segment2(profiles, start=1853, end=index_refill[2]),
            # job_segment(profiles, start=index_refill[2], end=-1),
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
