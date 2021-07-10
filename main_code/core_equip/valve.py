"""
Valve Class



config:
                                                    zero is closed or no port
    * "2"       on/off valve                        (1,2) or (0,0)
    * "3L"      3 way L or selector valve           (1,2) or (2,3)
    * "3LZ"     3 way L valve                       (1,2) or (2,3) or (3,0) or (0,1)
    * "3SZ"     3 way L or selector valve           (1,2) or (2,0) or (2,3)
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

"""

valve_config_options = {
    "2": [(1, 2), (0, 0)],
    "3L": [(1, 2), (2, 3)],
    "3LZ": [(1, 2), (2, 3), (3, 0), (0, 1)],
    "3TZ": [(0, 1, 2), (1, 2, 3), (2, 3, 0), (1, 0, 3)],
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


class Valve:
    def __init__(self,
                 name: str = None,
                 config: str = "2",
                 ports: list[str] = None,
                 **kwargs
                 ):
        """
        Core ChemBot Class: Valve
        :param name: any unique name for valve
        :param config: see above for options
        :param ports:
        :param kwargs:
                        * custom valve config
        """

        # Intialization
        self.name = name
        self.config = None
        self.positions = None
        self.num_ports = None
        self._config_check(config, **kwargs)



        # Track current state
        self.state = None



    def __repr__(self):
        return f"Valve: {self.name}\n\tport: {self.port}\n\t position: {self.position}"

    def move(self, pos: str):
        ...

    def move_next(self):
        ...

    def move_back(self):
        ...

    def _config_check(self, config, valve_options=None):
        # users can provide custom valve configurations if not supported in the list above
        if valve_config_options is None:
            valve_options = valve_config_options

        # Check if config is string
        if type(config) == str:
            # Check if valid valve option
            if config in valve_config_options.keys():
                self.config = config
                if config[-1] == "S":
                    self.positions = self._selector_valve(config)
                else:
                    self.positions = valve_config_options
                return None
            else:
                return ValueError(f"")
        else:
            return TypeError(f"")

    @staticmethod
    def _selector_valve(config: str) -> list[tuple]:
        """
        Given "#S" return position list for valve
        :param config:
        :return:
        """
        return [(1, i) for i in range(int(config[0]))]


if __name__ == '__main__':
    ...
