import abc
import logging

from chembot.configuration import config
from chembot.equipment.valves.valve_configuration import ValveConfiguration, ValvePosition
from chembot.equipment.equipment import Equipment

logger = logging.getLogger(config.root_logger_name + ".valve")


class Valve(Equipment, abc.ABC):
    def __init__(self,
                 name: str,
                 configuration: ValveConfiguration
                 ):
        super().__init__(name=name)
        self.configuration = configuration

        self.position: ValvePosition = self.configuration.positions[0]

    def __repr__(self):
        return f"\nValve: {self.name}\n" \
               f"\tconfig: {self.configuration}\n"\
               f"\tstate: {self.state}\n"\
               f"\tcurrent position: {self.position}\n"

    def _activate(self):
        self._move(self.configuration.positions[0])

    def read_position(self) -> ValvePosition:
        return self.position

    def write_move(self, position: int | str | ValvePosition):
        if not isinstance(position, ValvePosition):
            position = self.configuration[position]
        self._move(position)

        self.position = position

    def write_move_next(self):
        """
        Move to forward a valve position. (Will loop around.)
        :return:
        """
        if self.position is self.configuration.positions[-1]:
            position = 0  # loop around
        else:
            position = self.position.id_ + 1
        self.write_move(position)

    def write_move_back(self):
        """
        Move to back a valve position. (Will loop around.)
        :return:
        """
        if self.position is self.configuration.positions[0]:
            position = self.configuration.number_of_positions - 1  # loop around
        else:
            position = self.position.id_ - 1
        self.write_move(position)

    @abc.abstractmethod
    def _move(self, position: ValvePosition):
        ...
