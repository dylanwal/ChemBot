
import time

start = time.perf_counter()

a = time.time() -1
for i in range(1_000_000):
    if time.time() == a:
        print("t")

end = time.perf_counter()
print(end-start)
