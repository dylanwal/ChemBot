
import time


def main(n: int, m: int):
    loop_tuple = tuple(range(n))
    start = time.perf_counter()
    for _ in range(m):
        for i in loop_tuple:
            a = loop_tuple[i]
    end = time.perf_counter()
    print(end-start)

    start = time.perf_counter()
    for _ in range(m):
        for i in range(n):
            a = loop_tuple[i]
    end = time.perf_counter()
    print(end-start)


if __name__ == "__main__":
    main(2, 10_000_000)

