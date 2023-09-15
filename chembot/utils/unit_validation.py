
from unitpy import Quantity


def validate_quantity(quantity: Quantity, dimensionality, error_label: str, positive: bool = False):
    if quantity.dimensionality != dimensionality:
        raise ValueError(
            f"{error_label}: Invalid unit dimensionality.\n"
            f"Given: {quantity.dimensionality}\n"
            f"Expected: {dimensionality}"
        )
    if positive:
        if quantity.v < 0:
            raise ValueError(f"{error_label}: Can't be less than 0.\n")
