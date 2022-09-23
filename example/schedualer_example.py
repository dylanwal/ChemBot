import time
import threading

from chembot.utils.event_scheduler import EventScheduler


def delay1(arg):
    print(f"{arg} delay1: start {time.time()}")
    time.sleep(1)
    print(f"{arg} delay1: end {time.time()}")


def delay2(arg):
    print(f"{arg} delay2: start {time.time()}")
    time.sleep(2)
    print(f"{arg} delay2: end {time.time()}")


def run_threaded(job_func, *args, **kwargs):
    job_thread = threading.Thread(target=job_func, args=args, kwargs=kwargs)
    job_thread.start()


def main():
    sched = EventScheduler()
    sched.start()
    print("start")

    now = time.time()
    actions = [
        [now + 1, delay1],
        [now + 3, delay2],
        [now + 5, delay1],
        [now + 7, delay1],
    ]
    for t, action in actions:
        sched.enterabs(t, action, args=(1,))
        sched.enterabs(t, action, args=(2,))

    print("now: ", now)

    while not sched.empty():
        print("sleep")
        time.sleep(0.3)

    print("hi")
    sched.stop(hard_stop=True)
    print("end")


if __name__ == "__main__":
    main()
