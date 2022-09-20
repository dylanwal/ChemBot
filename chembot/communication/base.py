
import abc


class Communication(abc.ABC):
    def write(self, message: str):
        ...

    def read(self, bytes_):
        ...
