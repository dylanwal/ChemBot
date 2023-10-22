import threading
import time


class Buffer:
    def __init__(self):

        self.save_thread = threading.Thread(target=self.thread_func)
        self.save_thread.start()

    def thread_func(self):
        index = -1
        main_thread = threading.main_thread()
        while True:
            index += 1
            time.sleep(0.05)
            if not main_thread.is_alive():
                print("thread break")
                break


def main():
    b = Buffer()

    for i in range(10):
        time.sleep(0.2)

    print("main_done")


if __name__ == "__main__":
    main()
