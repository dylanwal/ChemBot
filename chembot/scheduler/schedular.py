import time

from chembot.scheduler.schedule import Schedule


class Schedular:
    def __init__(self, timer: callable = None):
        self.timer = timer if timer is None else time.monotonic
        self.schedule = Schedule()

    def run(self):

        while True:
            pass

