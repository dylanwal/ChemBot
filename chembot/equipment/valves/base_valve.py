"""
Valve Class

"""
from abc import ABC, abstractmethod
import re

from chembot.reference_data.valve_configs import valve_configs
from equipment.equipment import Equipment


class Valve(ABC, Equipment):
    valve_configs = valve_configs

    def __init__(self,
                 name: str,
                 config: str,
                 start_position: int = 1,
                 ports: dict[int:dict[str: any]] = None,
                 **kwargs
                 ):
        """
        Parameters
        ----------
        config: str
            see above for options
        ports: dictionary with {port_number(int): {"name": str, "link": ""}}
            name: any unique name for the port; Ex. into_reactor, gas_in, benzene_bottle
            link: name of equipment that is connected to the port
        start_position: int
            s
        kwargs
        """
        # Initialization
        super().__init__(name=name, **kwargs)

        # Will be all set in _config_check and _port_check
        self.config = None
        self.positions = None
        self.num_positions = None
        self.ports = None
        self.num_ports = None

        self._config_check(config, kwargs.get("valve_options"))
        self._port_check(ports)

    def __repr__(self):
        return f"\nValve: {self.name}\n" \
               f"\tconfig: {self.config}\n"\
               f"\tports:\n\t\t" + "\n\t\t".join("{}\t{}".format(k, v) for k, v in self.ports.items()) + "\n" \
               f"\tpositions:\n\t\t" + "\n\t\t".join(f"{i+1}\t{v}" for i, v in enumerate(self.positions)) + "\n" \
               f"\tstate: {self.state}\n"\
               f"\tcurrent position: {self.current_position}\n"

    @abstractmethod
    def actiavte(self, start_pos: int):
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


def main():
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


if __name__ == '__main__':
    main()
