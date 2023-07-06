from __future__ import annotations
import re
from typing import Iterator


def create_selector_valve(config: str) -> tuple[tuple[int, int]]:
    """
    Given "#S" return position list for valve
    """
    match = re.match(r'^\d+', config)
    if match:
        number_ports = int(match.group())
    else:
        raise ValueError(f"Invalid selector port configuration.\nInvalid: {config}")

    return tuple((1, i) for i in range(number_ports))


class ValvePort:
    __slots__ = ("id_", "_name", "blocked")

    def __init__(self, id_: int, name: str = None, blocked: bool = False):
        self.id_ = id_
        self._name = name
        self.blocked = blocked

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

    @property
    def name(self) -> str:
        if self._name is not None:
            return self._name
        return f"port_{self.id_}"

    @name.setter
    def name(self, name: str):
        self._name = name


class ValveChannel:
    __slots__ = ("connections",)

    def __init__(self, connections: tuple[ValvePort]):
        self.connections = connections

    def __str__(self):
        return " <--> ".join(str(port) for port in self.connections)

    def __repr__(self):
        return self.__str__()

    @property
    def number_ports(self) -> int:
        return len(self.connections)


class ValvePosition:
    def __init__(self,
                 id_: int,
                 channels: tuple[ValveChannel],
                 name: str = None,
                 setting=None
                 ):
        self.id_ = id_
        self.channels = channels
        self._name = name
        self.setting = setting

    def __str__(self):
        return " and ".join(str(port) for port in self.channels)

    def __repr__(self):
        return self.__str__()

    @property
    def name(self) -> str:
        if self._name is not None:
            return self._name
        return f"position_{self.id_}"

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def number_of_channels(self) -> int:
        return len(self.channels)


class ValveConfiguration:
    valve_configs = {
        "2": ((0, 2), (1, 3)),
        "3L": ((0, 1), (1, 2)),
        "3LZ": ((0, 1), (1, 2), (2, 3), (3, 0)),
        "3TZ": ((0, 1, 2), (1, 2, 3), (2, 3, 0), (1, 0, 3)),
        "3S": ((0, 1), (0, 2), (0, 3)),
        "4L": ((0, 1), (1, 2), (2, 3), (3, 0)),
        "4LL": (((0, 1), (2, 3)), ((1, 2), (3, 0)), ((2, 3), (0, 1)), ((3, 0), (1, 2))),
        "4T": ((0, 1, 2), (1, 2, 3), (2, 3, 0), (3, 0, 1)),
        "4": ((0, 2), (1, 3), (2, 0), (3, 1)),
        "6TL": (((0, 1), (2, 3), (4, 5)), ((6, 0), (1, 2), (3, 4))),  # sample valve
    }

    def __init__(self,
                 abbreviation: str,
                 positions: list[ValvePosition],
                 ports: list[ValvePort]
                 ):
        self.abbreviation = abbreviation
        self.positions = positions
        self.ports = ports

    def __str__(self):
        return " || ".join(str(port) for port in self.positions)

    def __repr__(self):
        return self.__str__()

    def __iter__(self) -> Iterator[ValvePosition]:
        return iter(self.positions)

    def __getitem__(self, item: int | str) -> ValvePosition:
        if isinstance(item, int):
            try:
                return self.positions[item]
            except IndexError as e:
                raise IndexError(f"Valve position outside valid range: [0, {self.number_of_positions-1}]")
        if isinstance(item, str):
            for pos in self.positions:
                if item == pos.name:
                    return pos
            raise ValueError(f"Invalid valve position name.\nInvalid position: {item}"
                             f"\nOptions: {[pos.name for pos in self.positions]}")
        raise ValueError(f"Invalid {type(self).__name__}.__getitem__ parameter.\nInvalid:{item}")

    @property
    def number_of_ports(self) -> int:
        return len(self.ports)

    @property
    def number_of_positions(self) -> int:
        return len(self.positions)

    @property
    def number_of_channels(self) -> int:
        return self.positions[0].number_of_channels

    @classmethod
    def get_configuration(cls, config: str) -> ValveConfiguration:
        """
        * blocked ports counted as well
              Key       description                          port connections (zero is closed or no port)
            * "2"       on off value                        (0, 2), (1, 3)
            * "3L"      3 way L or selector valve           (0, 1), (1, 2)
            * "3LZ"     3 way L valve                       (0, 1), (1, 2), (2, 3), (3, 0)
            * "3S"      3 way L or selector valve           (0, 1), (0, 2), (0, 3)
            * "3TZ"     3 way T valve                       (0, 1, 2), (1, 2, 3), (2, 3, 0), (1, 0, 3)
            * "4L"      4 way L valve                       (0, 1), (1, 2), (2, 3), (3, 0)
            * "4LL"     4 way double L valve                ((0, 1), (2, 3)), ((1, 2), (3, 0)), ((2, 3), (0, 1)),
                                                                ((3, 0), (1, 2))
            * "4T"      4 way T valve                       (1,2,3) or (2,3,4) or (3,4,1) or (4,1,2)
            * "4"       4 way straight valve                (0, 2), (1, 3), (2, 0), (3, 1)
            * "6TL"     6 way triple (sample valve)         ((0, 1), (2, 3), (4, 5)), ((6, 0), (1, 2), (3, 4))
            * "#S"      # selector valve (# can be any integer)
        """

        if config.endswith("S"):
            valve_config = create_selector_valve(config)
        elif config not in cls.valve_configs:
            valve_config = cls.valve_configs[config]
        else:
            raise ValueError("Invalid valve configuration.")

        # convert valve position tuple in python classes
        ports = []
        positions = []
        for i, position in enumerate(valve_config):
            positions.append(create_position(ports, position, i))

        return cls(config, positions, ports)


def create_position(ports: list[ValvePort], position, position_index: int):
    if not isinstance(position[0], tuple):
        position = tuple(position)

    channels = []
    for channel in position:
        channels.append(create_channel(ports, channel))

    return ValvePosition(position_index, tuple(channels))


def create_channel(ports: list[ValvePort], channel: tuple[int]) -> ValveChannel:
    connections = []
    for port in channel:
        if port > len(ports):
            ports.append(ValvePort(port))
        connections.append(ports[port])

    return ValveChannel(tuple(connections))
