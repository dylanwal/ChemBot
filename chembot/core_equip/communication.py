
import abc


class Communication(abc.ABC):
    def write(self):
        ...

    def read(self):
        ...
