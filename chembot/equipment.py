
import enum

from chembot.configuration import u
import chembot.utils.pint_utils as pint_utils


class GlobalIDs:
    objects = dict()

    def __init__(self):
        self.next_id = 0

    def get_id(self, obj) -> int:
        id_ = self.next_id
        self.objects[id_] = obj
        self.next_id += 1
        return id_


global_ids = GlobalIDs()


class EquipmentState(enum.Enum):
    offline = 0
    standby = 1
    scheduled_for_use = 2
    transient = 3
    running = 4
    shutting_down = 5
    cleaning = 6
    error = 7


class Equipment:
    """
    Base class for all equipment.

    """
    equipment_states = EquipmentState

    def __init__(self,
                 name: str = None,
                 min_temp: u.Quantity = u.Quantity(10, "degC"),
                 max_temp: u.Quantity = u.Quantity(30, "degC"),
                 min_pres: u.Quantity = u.Quantity(0, "kPa"),
                 max_pres: u.Quantity = u.Quantity(150, "kPa")
                 ):
        """
        Parameters
        ----------
        name: str
            any unique name for equipment
        min_temp: Pint.Quantity (temperature)
            minimum safe operating temperature (safety check)
        max_temp: Pint.Quantity (temperature)
            maximum safe operating temperature (safety check)
        min_pres: Pint.Quantity (temperature)
            minimum safe operating pressure (safety check)
        max_pres: Pint.Quantity (temperature)
            maximum safe operating pressure (safety check)
        """
        self._name = None
        self.name = name
        self._id_ = global_ids.get_id(self)

        self._state = None

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
    def id_(self) -> int:
        return self._id_

    @property
    def state(self) -> EquipmentState:
        return self._state

    @state.setter
    def state(self, state: EquipmentState):
        if type(state) is not EquipmentState:
            raise TypeError(f"Equipment state must be of type 'EquipmentState'. Given: {state}")
        self._state = state

    @property
    def min_temp(self):
        return self._min_temp

    @min_temp.setter
    @pint_utils.check_units("degC")
    def min_temp(self, min_temp):
        self._min_temp = min_temp

    @property
    def max_temp(self):
        return self._max_temp

    @max_temp.setter
    @pint_utils.check_units("degC")
    def max_temp(self, max_temp):
        self._max_temp = max_temp

    @property
    def min_pres(self):
        return self._min_pres

    @min_pres.setter
    @pint_utils.check_units("kPa")
    def min_pres(self, min_pres):
        self._min_pres = min_pres

    @property
    def max_pres(self):
        return self._max_pres

    @max_pres.setter
    @pint_utils.check_units("kPa")
    def max_pres(self, max_pres):
        self._max_pres = max_pres

    def _init_(self):
        pass


def run_local():
    equip = Equipment()
    print(equip)


if __name__ == "__main__":
    run_local()
