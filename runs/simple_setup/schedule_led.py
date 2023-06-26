from datetime import datetime, timedelta

from chembot.scheduler import JobSequence, JobConcurrent, Event, Schedule
from chembot.equipment.lights import LightPico
from chembot.scheduler.job_submitter import JobSubmitter


def blink(duration: timedelta, delay: timedelta = None):
    kwargs = {"power": 10}
    return JobSequence(
        [
            Event("deep_red", LightPico.write_power, timedelta(milliseconds=10), kwargs=kwargs),
            Event("deep_red", LightPico.write_off, timedelta(milliseconds=10), delay=duration),
        ],
        delay=delay,
        name="blink"
    )


def triple_blink(gap: timedelta, off: timedelta):
    return JobSequence(
        [
            blink(off),
            blink(off, delay=gap),
            blink(off, delay=gap)
        ],
        name="triple_blink"
    )


job_submitter = JobSubmitter()

job = blink(timedelta(seconds=3))
result = job_submitter.submit(job)
print(result)

job2 = triple_blink(gap=timedelta(seconds=0.5), off=timedelta(seconds=2))
# print(generate_job_flowchart(job2))
result = job_submitter.submit(job2)
print(result)

full_schedule = job_submitter.get_schedule()
print(full_schedule)
# gantt_chart = schedule_to_gantt_chart(full_schedule.schedule)
# app = create_app(gantt_chart)
# app.run(debug=True)

print("hi")
