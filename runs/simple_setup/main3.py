from datetime import datetime, timedelta

from chembot.scheduler import JobSequence, JobConcurrent, Event, Schedule
from chembot.equipment.lights import LightPico
from chembot.scheduler.job_submitter import JobSubmitter


def blink(duration: timedelta):
    return JobSequence(
        [
            Event("on_board_LED", LightPico.write_off, timedelta(milliseconds=10)),
            Event("on_board_LED", LightPico.write_on, timedelta(milliseconds=10), delay=duration),
        ]
    )


job = blink(timedelta(seconds=10))

job_submitter = JobSubmitter()
result = job_submitter.submit(job)
print(result)
print("hi")
