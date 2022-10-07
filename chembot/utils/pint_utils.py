from functools import wraps

from chembot.errors import EquipmentError
from chembot.configuration import u


def quantity_approx_equal(quantity1: u.Quantity, quantity2: u.Quantity, cutoff: float = 0.02) -> bool:
    """ Returns T/F for any two quantities"""
    if not isinstance(quantity1, u.Quantity) or not isinstance(quantity2, u.Quantity):
        return False

    if quantity1.dimensionality == quantity2.dimensionality:
        if quantity2.to_base_units().m == 0:  # avoid divide by zero error
            if quantity1.to_base_units().m == 0:
                return True
            return False

        if abs((quantity1 - quantity2) / quantity2) <= cutoff:
            return True

    return False


def quantity_difference(quantity1: u.Quantity, quantity2: u.Quantity) -> int | float:
    """ Returns absolute difference between quantities. """
    if isinstance(quantity1, (int, float)):
        quantity1 = u.Quantity(quantity1)
    if isinstance(quantity2, (int, float)):
        quantity2 = u.Quantity(quantity2)

    if not isinstance(quantity1, u.Quantity) or not isinstance(quantity2, u.Quantity) or \
            quantity1.dimensionality != quantity2.dimensionality:
        return 1

    if quantity2.to_base_units().m == 0:  # avoid divide by zero error
        if quantity1.to_base_units().m == 0:
            return True
        return False

    return abs((quantity1 - quantity2) / quantity2)


def check_units(unit: u.Unit | str):
    """
    """
    if type(unit) is str:
        unit = u.Unit(unit)
    if type(unit) is not u.Unit:
        raise TypeError("'unit' for 'check_unit' is wrong type")

    def check_units_decorator(func):
        @wraps(func)
        def _check_units(self, value: u.Quantity):
            if type(value) is not u.Quantity:
                raise EquipmentError(self, f"{func.__name__} requires a 'Pint.Quantity'. Given: {type(value)}")
            if unit.dimensionality != value.dimensionality:
                raise EquipmentError(self, f"{func.__name__}, {value} has the wrong units. Expected: {unit}")

            return func(self, value)
        return _check_units
    return check_units_decorator
