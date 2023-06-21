from datetime import datetime, timedelta

from chembot.scheduler import JobSequence, Event, Job, Schedule, JobSubmitResult
from chembot.scheduler.validate import validate_job
from chembot.equipment.lights import LightPico
from chembot.communication.serial_pico import PicoSerial
from chembot.equipment.equipment_interface import EquipmentRegistry


def example_schedule() -> Job:
    return JobSequence(
        [
            Event("on_board_LED", LightPico.write_off, timedelta(milliseconds=10)),
            Event("on_board_LED", LightPico.write_on, timedelta(milliseconds=10), delay=timedelta(seconds=10)),
        ]
    )


def main():
    job = example_schedule()
    schedule = Schedule.from_job(job)
    result = JobSubmitResult(job.id_)
    registry = EquipmentRegistry()
    registry.register_equipment("on_board_LED", LightPico)
    registry.register_equipment("pico_serial", PicoSerial)

    validate_job(schedule, registry, result)

    print(result)


if __name__ == "__main__":
    main()
