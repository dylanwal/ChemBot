import threading
import time

import numpy as np


def add(a: np.ndarray, index: int):
    a[index] = a[index] + 1


def add_many(a: np.ndarray, index: int):
    for i in range(10_000):
        add(a, index)


def add_int(a: list[int], index: int):
    a[index] = a[index] + 1


def add_many_int(a: list[int], index: int):
    for i in range(10_000):
        add_int(a, index)


def read_only(a, b):
    for i in range(10_000):
        b[1] += a[1]


def main():
    a = np.linspace(0, 9, 10, dtype="int")
    b = np.linspace(0, 9, 10, dtype="int")

    # save_thread = threading.Thread(target=read_only, args=(a, b))
    # save_thread.start()
    read_only(a,b)

    add_many(a, 0)
    print("run")
    # save_thread.join()
    if a[0] != b[1]-1:
        print(a)
        print(b)


if __name__ == "__main__":
    start = time.process_time()
    for i in range(100):
        main()
    end = time.process_time()
    print("time: ", end-start)