import sys
import time
import pickle

from pympler import asizeof


class AA:
    def __init__(self, a, b):
        self.a = a
        self.b = b


class BB(AA):
    def __init__(self, a, b, c, d):
        super().__init__(a, b)
        self.c = c
        self.d = d


class CC:
    def __init__(self, a, b, c, d):
        self.a = a
        self.b = b
        self.c = c
        self.d = d


class As:
    __slots__ = "a", "b"

    def __init__(self, a, b):
        self.a = a
        self.b = b


class Bs(As):
    __slots__ = "c", "d"

    def __init__(self, a, b, c, d):
        super().__init__(a, b)
        self.c = c
        self.d = d


class Cs:
    __slots__ = "a", "b", "c", "d"

    def __init__(self, a, b, c, d):
        self.a = a
        self.b = b
        self.c = c
        self.d = d


class Ds(AA):
    __slots__ = "a", "b", "c", "d"

    def __init__(self, a, b, c, d):
        super().__init__(a, b)
        self.c = c
        self.d = d


class Es(As):
    __slots__ = "a", "b", "c", "d"

    def __init__(self, a, b, c, d):
        super().__init__(a, b)
        self.c = c
        self.d = d

options = {
    "b_": BB,
    "c_": CC,
    "bs": Bs,
    "cs": Cs,
    "ds": Ds,
    "Es": Es,
}

n = 1000000
for op in options:
    start = time.process_time()
    for i in range(n):
        obj = options[op]("a", "b", "c", "d")
    end = time.process_time()
    print(op, end-start, sys.getsizeof(obj), asizeof.asizeof(obj))


    start = time.process_time()
    for i in range(int(n/10)):
        p_obj = pickle.dumps(obj)
    end = time.process_time()
    print(op, end-start, sys.getsizeof(p_obj), asizeof.asizeof(p_obj))


    start = time.process_time()
    for i in range(int(n/10)):
        l_obj = pickle.loads(p_obj)
    end = time.process_time()
    print(op, end-start, sys.getsizeof(l_obj), asizeof.asizeof(l_obj))

    print()

"""
b_ 1.0625 48 376
b_ 0.390625 95 96
b_ 0.3125 48 376

c_ 0.6875 48 376
c_ 0.390625 95 96
c_ 0.3125 48 376

bs 0.859375 64 288
bs 0.40625 98 104
bs 0.265625 64 288

cs 0.5 64 288
cs 0.390625 98 104
cs 0.4375 64 288

ds 1.203125 80 408
ds 0.8125 98 104
ds 0.328125 80 408

Es 1.0 80 304
Es 0.453125 98 104
Es 0.296875 80 304


cs is best as it smallest and fastest
bs is second best (slower than cs as it has the 'super' call)

"""