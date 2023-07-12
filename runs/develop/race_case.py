import threading

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


def main():
    a = [0] #np.linspace(0, 9, 10, dtype="int")

    save_thread = threading.Thread(target=add_many_int, args=(a, 0))
    save_thread.start()

    add_many_int(a, 0)
    print(a)


if __name__ == "__main__":
    main()
