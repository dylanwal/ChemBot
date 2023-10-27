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
    def flow_rate_cat(self):
        return self.profile[:, 4]

    @property
    def flow_rate_dmso(self):
        return self.profile[:, 5]

    @property
    def flow_rate_fl(self):
        return self.profile[:, 6]

    @staticmethod
    def get_volume(t: np.ndarray, flow_rate: np.ndarray):
        return np.trapz(x=t, y=flow_rate)


def load_profiles() -> DynamicProfile:
    # t, temp, light, flow_rate_mon, flow_rate_cat, flow_rate_dmso
    data = np.loadtxt(r"DW2_7_profiles.csv", delimiter=",")
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
        delay: timedelta = None,
        duration: bool = True
) -> JobConcurrent:
    return JobConcurrent(
        [job_flow(vol, flow, val, p, duration) for vol, flow, val, p in zip(volume, flow_rate, valves, pumps)],
        delay=delay  # to allow syringes to stabilize
    )


def steady_state(profile: DynamicProfile):
    mon_vol = float(profile.flow_rate_mon[0]) * Unit("ml") * 21  # (3*7min) * flowrate(ml/min) = ml|7min residence time
    cat_vol = float(profile.flow_rate_cat[0]) * Unit("ml") * 21
    fl_vol = float(profile.flow_rate_fl[0]) * Unit("ml") * 21
    dmso_vol = float(profile.flow_rate_dmso[0]) * Unit("ml") * 21

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
                    cat_vol,
                    fl_vol,
                    dmso_vol,
                ],
                flow_rate=[
                    1 * Unit("ml/min"),
                    1 * Unit("ml/min"),
                    1 * Unit("ml/min"),
                    1 * Unit("ml/min"),
                ],
                valves=[NamesValves.ONE, NamesValves.TWO, NamesValves.THREE, NamesValves.FOUR],
                pumps=[NamesPump.ONE, NamesPump.TWO, NamesPump.THREE, NamesPump.FOUR]
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
                    float(profile.flow_rate_cat[0]) * Unit("ml/min"),
                    float(profile.flow_rate_fl[0]) * Unit("ml/min"),
                    float(profile.flow_rate_dmso[0]) * Unit("ml/min"),
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
    t = profile.time[start: end]
    t = t - t[0]
    temp = profile.temp[start: end]
    light = profile.light[start: end]
    flow_rate_mon = profile.flow_rate_mon[start: end]
    flow_rate_cat = profile.flow_rate_cat[start: end]
    flow_rate_dmso = profile.flow_rate_dmso[start: end]
    flow_rate_fl = flow_rate_mon + flow_rate_cat + flow_rate_dmso

    mon_vol = profile.get_volume(t/60, flow_rate_mon) * Unit("ml")
    cat_vol = profile.get_volume(t/60, flow_rate_cat) * Unit("ml")
    fl_vol = profile.get_volume(t/60, flow_rate_fl) * Unit("ml")
    dmso_vol = profile.get_volume(t/60, flow_rate_dmso) * Unit("ml")

    # power is [0, 65535]
    light_profile = ContinuousEventHandlerProfile(LightPico.write_power, ["power"], (light * 65535).astype(np.int32), t)
    temp_profile = ContinuousEventHandlerProfile(PolyRecirculatingBath.write_set_point, ["temperature"], temp, t)
    _flow_rate_mon = tuple(f * Unit("ml/min") for f in flow_rate_mon)
    mon_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], _flow_rate_mon, t)
    _flow_rate_cat = tuple(f * Unit("ml/min") for f in flow_rate_cat)
    cat_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], _flow_rate_cat, t)
    _flow_rate_dmso = tuple(f * Unit("ml/min") for f in flow_rate_dmso)
    dmso_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], _flow_rate_dmso, t)
    _fl_flow_rate = tuple(f * Unit("ml/min") for f in flow_rate_fl)
    fl_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], _fl_flow_rate, t)

    return JobSequence(
        [
            job_fill_syringe_multiple(
                volume=[
                    mon_vol,
                    cat_vol,
                    fl_vol,
                    dmso_vol,
                ],
                flow_rate=[
                    1 * Unit("ml/min"),
                    1 * Unit("ml/min"),
                    1 * Unit("ml/min"),
                    1 * Unit("ml/min"),
                ],
                valves=[NamesValves.ONE, NamesValves.TWO, NamesValves.THREE, NamesValves.FOUR],
                pumps=[NamesPump.ONE, NamesPump.TWO, NamesPump.THREE, NamesPump.FOUR]
            ),

            job_flow_syringe_multiple(
                volume=[
                    mon_vol * 2,
                    cat_vol * 2,
                    fl_vol * 2,
                    dmso_vol * 2,
                ],
                flow_rate=[
                    float(flow_rate_mon[0]) * Unit("ml/min"),
                    float(flow_rate_cat[0]) * Unit("ml/min"),
                    float(flow_rate_fl[0]) * Unit("ml/min"),
                    float(flow_rate_dmso[0]) * Unit("ml/min"),
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
                        kwargs={"event_handler": cat_profile},
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
                        kwargs={"event_handler": dmso_profile},
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


def job_segment2(profile: DynamicProfile, start: int, end: int):
    t = profile.time[start: end]
    t = t - t[0]
    temp = profile.temp[start: end]
    light = profile.light[start: end]
    flow_rate_mon = profile.flow_rate_mon[start: end]
    flow_rate_cat = profile.flow_rate_cat[start: end]
    flow_rate_dmso = profile.flow_rate_dmso[start: end]
    flow_rate_fl = flow_rate_mon + flow_rate_cat + flow_rate_dmso

    mon_vol = profile.get_volume(t/60, flow_rate_mon) * Unit("ml")
    cat_vol = profile.get_volume(t/60, flow_rate_cat) * Unit("ml")
    fl_vol = profile.get_volume(t/60, flow_rate_fl) * Unit("ml")
    dmso_vol = profile.get_volume(t/60, flow_rate_dmso) * Unit("ml")

    # power is [0, 65535]
    light_profile = ContinuousEventHandlerProfile(LightPico.write_power, ["power"], (light * 65535).astype(np.int32), t)
    temp_profile = ContinuousEventHandlerProfile(PolyRecirculatingBath.write_set_point, ["temperature"], temp, t)
    _flow_rate_mon = tuple(f * Unit("ml/min") for f in flow_rate_mon)
    mon_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], _flow_rate_mon, t)
    _flow_rate_cat = tuple(f * Unit("ml/min") for f in flow_rate_cat)
    cat_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], _flow_rate_cat, t)
    _flow_rate_dmso = tuple(f * Unit("ml/min") for f in flow_rate_dmso)
    dmso_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], _flow_rate_dmso, t)
    _fl_flow_rate = tuple(f * Unit("ml/min") for f in flow_rate_fl)
    fl_profile = ContinuousEventHandlerProfile(
        SyringePumpHarvard.write_infusion_rate, ["flow_rate"], _fl_flow_rate, t)

    return JobSequence(
        [

            job_flow_syringe_multiple(
                volume=[
                    mon_vol * 2,
                    cat_vol * 2,
                    fl_vol * 2,
                    dmso_vol * 2,
                ],
                flow_rate=[
                    float(flow_rate_mon[0]) * Unit("ml/min"),
                    float(flow_rate_cat[0]) * Unit("ml/min"),
                    float(flow_rate_fl[0]) * Unit("ml/min"),
                    float(flow_rate_dmso[0]) * Unit("ml/min"),
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
                        kwargs={"event_handler": cat_profile},
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
                        kwargs={"event_handler": dmso_profile},
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


def job_droplets() -> JobSequence:
    profiles = load_profiles()
    # index_refill = [250, 583, 915, 1248, 1581, 1914, 2247]  # [41.68, 97.2, 152, 208, 263, 319, 374]
    index_refill = [583, 1248, 1914]

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
            # segment pre
            # steady_state(profiles),
            # # segment 1-8
            # job_segment(profiles, start=0, end=index_refill[0]),  # 41.68
            # job_segment(profiles, start=index_refill[0], end=index_refill[1]),  # 97.2
            # job_segment(profiles, start=index_refill[1], end=index_refill[2]),  # 152
            # # job_segment(profiles, start=index_refill[2], end=index_refill[3]),  # 208
            # # job_segment(profiles, start=index_refill[3], end=index_refill[4]),  # 263
            # # job_segment(profiles, start=index_refill[4], end=index_refill[5]),  # 319
            # # job_segment(profiles, start=index_refill[5], end=index_refill[6]),  # 374
            # job_segment(profiles, start=index_refill[2], end=-1),  # 374

            # job_segment2(profiles, start=1248, end=1914),  # 41.68
            # job_segment2(profiles, start=1914, end=2664),  # 97.2

            # segment post
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
