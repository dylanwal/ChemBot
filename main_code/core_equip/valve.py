"""
Valve Class



config:
      Key       description                          port connections (zero is closed or no port)
    * "2"       on/off valve                        (1,2) or (0,0)
    * "3L"      3 way L or selector valve           (1,2) or (2,3)
    * "3LZ"     3 way L valve                       (1,2) or (2,3) or (3,0) or (0,1)
    * "3Z"      3 way L or selector valve           (1,2) or (2,0) or (2,3)
    * "3TZ"     3 way T valve                       (0,1,2) or (1,2,3) or (2,3,0) or (1,0,3)
    * "4L"      4 way L valve                       (1,2) or (2,3) or (3,4) or (4,1)
    * "4LL"     4 way double L valve                ((1,2),(3,4)) or ((4,1),(2,3)) or ((2,1),(4,3)) or ((1,4),(3,2))
    * "4T"      4 way T valve                       (1,2,3) or (2,3,4) or (3,4,1) or (4,1,2)
    * "4"       4 way straight valve                (1,3) or (2,4) or (3,1) or (4,2)
    * "4S"      4 way selector                      (1,2) or (1,3) or (1,4)
    * "5S"      5 way selector                      (1,2) or (1,3) or (1,4) or (1,5)
    * "6D"      6 way double path valve             ((1,2),(4,5)) or ((2,3),(5,6)) or ((3,4),(6,1)) or ((4,5),(1,2)) or
                                                        ((5,6),(2,3)) or ((6,1),(3,4))
    * "6DL"     6 way double path limited valve     ((1,2),(4,5)) or ((2,3),(5,6))
    * "6TL"     6 way triple path limited valve     ((1,2),(3,4),(5,6)) or ((1,6),(2,3),(4,5))
    * "#S"      # selector valve (# can be any integer up to 12)

    Notes: written from the perspective of available rotations for a real valve

"""
from abc import ABC, abstractmethod
import re

from main_code.core_equip.equip import _Equip


valve_config_options = {
    "2": [(0, 0), (1, 2)],
    "3L": [(1, 2), (2, 3)],
    "3LZ": [(1, 2), (2, 3), (3, 0), (0, 1)],
    "3TZ": [(0, 1, 2), (1, 2, 3), (2, 3, 0), (1, 0, 3)],
    "3Z": [(1, 2), (2, 0), (2, 3)],
    "4L": [(1, 2), (2, 3), (3, 4), (4, 1)],
    "4LL": [((1, 2), (3, 4)), ((4, 1), (2, 3)), ((2, 1), (4, 3)), ((1, 4), (3, 2))],
    "4T": [(1, 2, 3), (2, 3, 4), (3, 4, 1), (4, 1, 2)],
    "4": [(1, 3), (2, 4), (3, 1), (4, 2)],
    "4S": [],  # will be calculated with function _selector_valve
    "5S": [],  # will be calculated with function _selector_valve
    "6D": [((1, 2), (4, 5)), ((2, 3), (5, 6)), ((3, 4), (6, 1)), ((4, 5), (1, 2)), ((5, 6), (2, 3)), ((6, 1), (3, 4))],
    "6DL": [((1, 2), (4, 5)), ((2, 3), (5, 6))],
    "6TL": [((1, 2), (3, 4), (5, 6)), ((1, 6), (2, 3), (4, 5))],
    "6S": [],  # will be calculated with function _selector_valve
    "7S": [],  # will be calculated with function _selector_valve
    "8S": [],  # will be calculated with function _selector_valve
    "9S": [],  # will be calculated with function _selector_valve
    "10S": [],  # will be calculated with function _selector_valve
    "11S": [],  # will be calculated with function _selector_valve
    "12S": [],  # will be calculated with function _selector_valve
}


class _Valve(_Equip, ABC):

    def __init__(self, config: str, ports: dict[int:dict[str: any]], start_pos: int = 1, **kwargs):
        """
        Core ChemBot Class: Valve
        :param config: see above for options
        :param ports: dictionary with {port_number(int): {"name": str, "link": ""}}
            name: any unique name for the port; Ex. into_reactor, gas_in, benzene_bottle
            link: name of equipment that is connected to the port

        If valve configuration not in provide ones use **kwargs to provide custom valve config: valve_options.
        """

        # Initialization
        super().__init__(**kwargs)

        # Will be all set in _config_check and _port_check
        self.config = None
        self.positions = None
        self.num_positions = None
        self.ports = None
        self.num_ports = None
        self._config_check(config, kwargs.get("valve_options"))
        self._port_check(ports)

        # Track current state
        self.initialize(start_pos=start_pos)
        self.current_position = start_pos

    def __repr__(self):
        return f"\nValve: {self.name}\n" \
               f"\tconfig: {self.config}\n"\
               f"\tports:\n\t\t" + "\n\t\t".join("{}\t{}".format(k, v) for k, v in self.ports.items()) + "\n" \
               f"\tpositions:\n\t\t" + "\n\t\t".join(f"{i+1}\t{v}" for i, v in enumerate(self.positions)) + "\n" \
               f"\tstate: {self.state}\n"\
               f"\tcurrent position: {self.current_position}\n"

    @abstractmethod
    def initialize(self, start_pos: int):
        """Needs to be defined in subclass."""
        self.state = "standby"

    @abstractmethod
    def execute(self, position: int):
        """Needs to be defined in subclass."""
        pass

    def move(self, position: int):
        """
        Moves valve to position specified.
        :param position: position
        :return:
        """
        if 1 <= position <= self.num_positions:
            self.execute(position)
            self.current_position = position
        else:
            raise ValueError(f"Position outside valid range: [1, {self.num_positions}]")

    def move_next(self):
        """
        Move to forward a valve position. (Will loop around.)
        :return:
        """
        if self.current_position == self.num_positions:
            next_position = 1  # loop around to position 1
        else:
            next_position = self.current_position + 1
        self.move(position=next_position)

    def move_back(self):
        """
        Move to back a valve position. (Will loop around.)
        :return:
        """
        if self.current_position == 1:
            next_position = self.num_positions  # loop around to position 1
        else:
            next_position = self.current_position - 1
        self.move(position=next_position)

    def _config_check(self, config, valve_options=None):
        # users can provide custom valve configurations if not supported in the list above
        if valve_options is None:
            valve_options = valve_config_options

        # Check if config is string
        if type(config) == str:
            # Check if valid valve option
            if config in valve_options.keys():

                # setting config
                self.config = config
                # setting positions
                if config[-1] == "S":
                    self.positions = self._selector_valve(config)
                else:
                    self.positions = valve_options[config]
                # setting num_positions
                self.num_positions = len(self.positions)
                return None

            else:
                raise ValueError(f"")
        else:
            raise TypeError(f"")

    @staticmethod
    def _selector_valve(config: str) -> list[tuple]:
        """
        Given "#S" return position list for valve
        :param config:
        :return:
        """
        return [(1, i) for i in range(int(config[0]))]

    @staticmethod
    def _cal_num_ports(config: str) -> list[tuple]:
        """
        Given position list, get number of ports.
        It includes zero as a port.
        :param config:
        :return:
        """
        return [(1, i) for i in range(int(config[0]))]

    def _port_check(self, ports):
        """
        Checks user provided port to make sure its in the right format before setting
        :param ports:
        :return:
        """
        # setting num of ports
        self.num_ports = int(re.split('(\d+)', self.config)[1])

        # check to see if enough ports were given
        if self.num_ports == len(ports.keys()):
            # check that port numbering is correct
            if list(ports.keys()) != [i for i in range(1, self.num_ports+1)]:
                raise ValueError(f"Port number does not match expected. received: {list(ports.keys())}, "
                                 f"expected: {[i for i in range(1, self.num_ports+1)]}")
            # checking other stuff

            self.ports = ports
        else:
            raise ValueError(f"{self.config} requires {self.num_ports}, but {len(ports.keys)} were given.")


class ValveVis(_Valve):
    """
    This is for testing only.
    """
    def initialize(self, start_pos: int):
        """Needs to be defined in subclass."""
        self.state = "standby"

    def execute(self, position):
        """Needs to be defined in subclass."""
        pass


if __name__ == '__main__':
    ports = {
        1: {
            "name": "air_source",
            "link": "air_source"
        },
        2: {
            "name": "to_reactor",
            "link": "reactor"
        },
        3: {
            "name": "syringe_pump",
            "link": "air_pump"
        }
    }
    config = '3Z'
    name = "air_valve"

    valve = ValveVis(name=name, config=config, ports=ports)
    print(valve)
