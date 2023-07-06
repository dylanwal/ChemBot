import abc

from chembot.equipment.equipment import Equipment


class Sensor(Equipment, abc.ABC):

    @abc.abstractmethod
    def write_measure(self):
        pass
