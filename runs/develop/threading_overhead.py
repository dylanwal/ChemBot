import time
import threading


class ThreadWithReturnValue(threading.Thread):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):
        threading.Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, timeout=None):
        threading.Thread.join(self, timeout)
        return self._return


def timeout(callable_: callable, timeout: int = None):
    thread_ = ThreadWithReturnValue(target=task)
    thread_.start()
    return thread_.join(timeout=timeout)


def task():
    # time.sleep(0.0001)
    return 1


def main():

    start = time.perf_counter()
    for i in range(10_000):
        task()
    end = time.perf_counter()
    print("no thread:", end-start)

    start = time.perf_counter()
    for i in range(10_000):
        timeout(task, 1)
    end = time.perf_counter()
    print("with thread:", end-start)


if __name__ == "__main__":
    main()
