import inspect
import os
import sys

from chembot.utils.logger import logger


def get_unit_registry():
    """
    Gets object from Python stack/globals
    Stops at first object it finds
    """
    stack = inspect.stack()
    for frame in stack:
        attrs: dict = frame.frame.f_locals
        for attr in attrs.values():
            if hasattr(attr, "_REGISTRY"):
                return attr._REGISTRY
    else:
        mes = "Pint UnitRegistry not found."
        raise Exception(mes)


def check_for_pint():
    """ Check for Pint
    Pint's requires a Unit Registry to be defined. However, Unit Registries are not interoperable and will throw
    errors if a unit from one registry is used in another. So we go looking to see if one has been created,
    and if it hasn't we will make one!
    Returns
    -------
    UnitRegistry
    """
    modules = sys.modules
    if "pint" in modules:
        logger.info("'Pint' module found in stack. (you have 'import pint' somewhere in your code).")
        # get unit registry
        try:
            u_ = get_unit_registry()
            logger.info("\033[32m Unit registry found. :) \033[0m")
            return u_
        except Exception:
            logger.warning("Pint unit registry not found in stack. Loading 'unit_parser' registry. (Note: "
                           "Pint unit registries are not interoperable. ")

    # if no pint found, load local
    import pint
    current_path = os.path.dirname(os.path.realpath(__file__))
    u_ = pint.UnitRegistry(autoconvert_offset_to_baseunit=True,
                           filename=os.path.join(current_path, "support_files", "unit_registry.txt"))
    u_.default_format = "~"
    return u_


# set pint units
u = check_for_pint()
U = Unit = u.Unit
Q = Quantity = u.Quantity

#######################################################################################################################


class Configurations:
    def __init__(self):
        self.encoding = "UTF-8"
        self.sig_fig_pump = 3


configuration = Configurations()
