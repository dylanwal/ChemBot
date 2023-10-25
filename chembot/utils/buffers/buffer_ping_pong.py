import pathlib
import queue
import threading
import numpy as np
from typing import Sequence


class SavingThread:
    def __init__(self, path: pathlib.Path):
        self._path = None
        self.path = path
        self.data_queue = queue.Queue(maxsize=1)
        self.thread = threading.Thread(target=self._run)
        self.thread.start()
        self.file_counter = 0

    @property
    def path(self) -> pathlib.Path | None:
        return self._path

    @path.setter
    def path(self, path: str | pathlib.Path):
        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path)
        if not path.suffix == ".csv":
            path = path.with_suffix(".csv")
        self._path = path

    def add_data_to_queue(self, data: np.ndarray):
        """ Blocking if queue is full """
        self.data_queue.put(data)

    def _get_file_path(self) -> pathlib.Path:
        path = self.path
        path = path.with_stem(path.stem + "_" + str(self.file_counter))

        counter = 0
        while True:
            if path.exists():
                path = path.with_stem(path.stem + "_" + str(counter))
            else:
                break

        return path

    def _run(self):
        main_thread = threading.main_thread()
        while True:
            try:
                data = self.data_queue.get(timeout=0.25)
                self._save(data)
            except queue.Empty:
                if not main_thread.is_alive() and self.data_queue.empty():
                    break

    def _save(self, data):
        np.savetxt(self._get_file_path(), data, delimiter=",")
        self.file_counter += 1


class PingPongBuffer:
    def __init__(self, path: pathlib.Path, capacity: int = 50_000):
        self.buffer_active = None
        self.buffer_passive = None
        self.capacity = capacity
        self.position = 0
        self.total_rows = 0
        self.saving_thread = SavingThread(path)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save_all()

    def add_data(self, data: int | float | Sequence[int | float] | np.ndarray):
        try:
            # try-except is used for improved performance
            self.buffer_active[self.position, :] = data
            self.position += 1
            self._check()  # will raise an Attribute error if no buffer created yet
        except TypeError as _:
            self._create_buffer(data)
            self.buffer_active[self.position, :] = data
            self.position += 1

        self.total_rows += 1

    def _check(self):
        if self.position == len(self.buffer_active):
            self.buffer_active, self.buffer_passive = self.buffer_passive, self.buffer_active
            self.position = 0
            self.save_passive()

    def _create_buffer(self, data: int | float | Sequence[int | float] | np.ndarray):
        if isinstance(data, int):
            self.buffer_active = np.zeros((self.capacity, 1), dtype=np.int64)
        elif isinstance(data, float):
            self.buffer_active = np.zeros((self.capacity, 1), dtype=np.float64)
        elif isinstance(data, list) or isinstance(data, tuple):
            self.buffer_active = np.zeros((self.capacity, len(data)))
        elif isinstance(data, np.ndarray):
            self.buffer_active = np.zeros((self.capacity, data.shape[0]), dtype=data.dtype)
        else:
            raise TypeError(f"Invalid type.\t\nGive: {data}\t\nExpected: int | float | np.ndarray\n")

        self.buffer_passive = np.zeros_like(self.buffer_active)

    def save_all(self):
        self.saving_thread.add_data_to_queue(self.buffer_active[:self.position])
        # buffer_passive should already be saved

    def save_passive(self):
        self.saving_thread.add_data_to_queue(self.buffer_passive)


def main():
    path = pathlib.Path(__file__).parent / "data.csv"
    with PingPongBuffer(path, capacity=105) as buffer:
        for i in range(110):
            buffer.add_data((i, 1.2))

    print("done")


if __name__ == "__main__":
    main()
