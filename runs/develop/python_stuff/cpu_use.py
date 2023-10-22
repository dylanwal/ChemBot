import os

os.sched_setaffinity(0, {0})

a = 1
while True:
    a = a + 1
    a = a - 1