import sys
import time
import pathlib

import numpy as np

from chembot.utils.buffers.buffer_ring import BufferRing, BufferRingTime, BufferRingSavable, BufferRingTimeSavable


def data_generator(columns: int = 1):

    while True:
        time.sleep(np.random.randint(0, 5) * 0.001)
        yield np.random.rand(columns)


def t_BufferRing(m: int = 1, n: int = 15, l: int = 10):
    gen_ = data_generator(m)

    buffer = BufferRing(length=l)
    answer = np.empty((l, m), dtype=np.float64)
    for i in range(n):
        data = next(gen_)
        # print(data)
        buffer.add_data(data)
        if i >= n-l:
            answer[i - (n-l), :] = data

    if (answer == data).all():
        print("t_BufferRing: BAD!")
    else:
        print("t_BufferRing: Pass")


def t_BufferRingTime(m: int = 1, n: int = 15, l: int = 10):
    gen_ = data_generator(m)

    buffer = BufferRingTime(length=l)
    answer = np.empty((l, m), dtype=np.float64)
    for i in range(n):
        data = next(gen_)
        # print(data)
        buffer.add_data(data)
        if i >= n-l:
            answer[i - (n-l), :] = data

    if answer.shape == data.shape or (answer == data).all():
        print("t_BufferRingSavable: Pass!")
    else:
        print("t_BufferRingSavable: BAD!")


def t_BufferRingSavable(path, m: int = 3, n: int = 15, l: int = 10):
    gen_ = data_generator(m)

    buffer = BufferRingSavable(path, length=l)
    answer = np.empty((n, m), dtype=np.float64)
    for i in range(n):
        data = next(gen_)
        # print(data)
        buffer.add_data(data)
        answer[i, :] = data

    buffer.save_all()
    time.sleep(1)
    data = np.genfromtxt(path, delimiter=',')
    if answer.shape == data.shape or (answer == data).all():
        print("t_BufferRingSavable: Pass!")
    else:
        print("t_BufferRingSavable: BAD!")


def main():
    # t_BufferRing()
    # t_BufferRing(3)
    # t_BufferRingTime()
    # t_BufferRingTime(3)
    root = pathlib.Path(sys.argv[0])
    path = pathlib.Path(root.parent) / "buffer_test.csv"
    t_BufferRingSavable(path)


if __name__ == "__main__":
    main()
