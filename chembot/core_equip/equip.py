"""


'Class Equip' is an abstract base class. Abstract base classes exist to be inherited, but never instantiated.
The abc module prevents instantiation.
The leading underscores in the class name is to communicate that objects of that class should not be created by the user.
"""

from abc import ABC


class _Equip(ABC):
    def __init__(self,
                 name,
                 min_temp,
                 max_temp,
                 min_pres,
                 max_pres
                 ):
        """

        :param name: any unique name for equipment
        :param min_temp: minimum safe operating temperature (safety check)
        :param max_temp: maximum safe operating temperature (safety check)
        :param min_pres: minimum safe operating pressure (safety check)
        :param max_pres: maximum safe operating pressure (safety check)
        """
        self._name = None
        self.name = name
        self._state = None  # "standby", "running"

        self._min_temp = None
        self.min_temp = min_temp
        self._max_temp = None
        self.max_temp = max_temp
        self._min_pres = None
        self.min_pres = min_pres
        self._max_pres = None
        self.max_pres = max_pres

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state

    @property
    def min_temp(self):
        return self._min_temp

    @min_temp.setter
    def min_temp(self, min_temp):
        self._min_temp = min_temp

    @property
    def max_temp(self):
        return self._max_temp

    @max_temp.setter
    def max_temp(self, max_temp):
        self._max_temp = max_temp

    @property
    def min_pres(self):
        return self._min_pres

    @min_pres.setter
    def min_pres(self, min_pres):
        self._min_pres = min_pres

    @property
    def max_pres(self):
        return self._max_pres

    @max_pres.setter
    def max_pres(self, max_pres):
        self._max_pres = max_pres
