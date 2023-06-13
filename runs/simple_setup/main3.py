from datetime import datetime, timedelta

from chembot.scheduler import JobSequence, JobSubmitter, JobConcurrent, Event, Schedule
from chembot.equipment.lights import LightPico


def blink(duration: timedelta):
    return JobSequence(
        [
            Event("deep_red", LightPico.write_on, timedelta(milliseconds=10)),
            Event("deep_red", LightPico.write_on, timedelta(milliseconds=10), delay=duration),
        ]
    )


job = blink(timedelta(seconds=10))

job_submitter = JobSubmitter()
result = job_submitter.submit(job)
print(result)
