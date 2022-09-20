import math
import enum

from chembot import configuration, logger
import chembot.core_equip.communication as communication
import chembot.utils.sig_figs as sig_figs
from chembot.errors import PumpError


class PumpFlowProfile:
    def __init__(self):
        pass





def get_syringe_parameters(diameter: float | None, max_volume: float | None, max_pull: float | None) \
        -> tuple[float, float, float]:
    """
    This function completes the syringe calculation as only 2 of 3 values are needed.
    V = pi * r**2 * L

    Parameters
    ----------
    diameter: float, None

    max_volume: float, None

    max_pull: float, None

    Returns
    -------
    diameter: float

    max_volume: float

    max_pull: float

    """
    if isinstance(diameter, float):
        check_diameter(diameter)

        if isinstance(max_volume, float):
            check_max_volume(max_volume)
            max_pull = max_volume / (math.pi * (diameter/2)**2)
            return diameter, max_volume, max_pull
        elif isinstance(max_pull, float):
            check_max_pull(max_pull)
            max_volume = math.pi * (diameter/2)**2 * max_pull
            return diameter, max_volume, max_pull

    elif isinstance(max_volume, float):
        check_max_volume(max_volume)

        if isinstance(max_pull, float):
            check_max_pull(max_pull)
            diameter = 2 * math.sqrt(max_volume / (math.pi*max_pull))
            return diameter, max_volume, max_pull

    text_insufficient = "In"
    raise PumpError(text_insufficient)


def check_diameter(diameter: float):
    if diameter <= 0:
        raise PumpError("diameter can't be negative")


def check_max_volume(max_volume: float):
    if max_volume <= 0:
        raise PumpError("max volume can't be negative")


def check_max_pull(max_pull: float):
    if max_pull <= 0:
        raise PumpError("max volume can't be negative")


class States(enum.Enum):
    offline = 0
    standby = 1
    running = 2


class ControlMethod(enum.Enum):
    flow_rate = 0
    pressure = 1


class Pump:
    instances = []
    states = States
    control_method = ControlMethod

    def __init__(
            self,
            serial_line: communication.Communication,
            name: str = "pump",
            diameter: float = None,  # units: cm
            max_volume: float = None,  # units: ml
            max_pull: float = None,  # units: cm
            number_syringe: int = 1,
            control_method: ControlMethod = ControlMethod.flow_rate
    ):
        self._add_instance_()

        self.serial_line = serial_line
        self.name = name

        self._state = None
        self._diameter = None
        self._max_volume = None
        self._max_pull = None
        self._volume = None  # units: ml
        self._flow_rate = None  # units: ml/min
        self._x = None
        self._number_syringe = None
        self.number_syringe = number_syringe
        self.control_method = control_method
        self._set_syringe_settings(diameter, max_volume, max_pull)

        logger.info(repr(self))

    def __repr__(self):
        text = f"Pump: {self.name} \n"
        text += f"current state: {self.state} \n"
        text += f"\tdiameter: {sig_figs.sig_figs(self._diameter, configuration.sig_fig)} cm\n"
        text += f"\tmax_volume: {sig_figs.sig_figs(self._max_volume, configuration.sig_fig)} ml\n"
        text += f"\tmax_pull: {sig_figs.sig_figs(self._max_pull, configuration.sig_fig)} cm\n"
        text += f"\tvolume: {sig_figs.sig_figs(self._volume, configuration.sig_fig)} ml\n"
        text += f"\tflow_rate: {sig_figs.sig_figs(self._flow_rate, configuration.sig_fig)} ml/min\n"
        text += f"\tposition: {sig_figs.sig_figs(self._x, configuration.sig_fig)} ml \n"

        return text

    def _add_instance_(self):
        self.__class__.instances.append(self)
        self.syringe_count = 0
        self.syringe_setup = False

    def _set_syringe_settings(self, diameter: float | None, max_volume: float | None, max_pull: float | None):
        diameter, max_volume, max_pull = get_syringe_parameters(diameter, max_volume, max_pull)
        self.diameter = diameter
        self.max_volume = max_volume
        self.max_pull = max_pull

        self._x = 0
        self.volume = 0  # units: ml
        self.flow_rate = 0  # units: ml/min
        self.state = PumpState.standby

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state: PumpState):
        self._state = state

    @property
    def number_syringe(self):
        return self._number_syringe

    @number_syringe.setter
    def number_syringe(self, number_syringe: int):
        self._number_syringe = number_syringe

    @property
    def diameter(self):
        return self._diameter

    @diameter.setter
    def diameter(self, diameter: float):
        diameter, max_volume, max_pull = get_syringe_parameters(diameter, self.max_volume, self.max_pull)
        self.diameter = diameter

    @property
    def max_volume(self):
        return self._max_volume

    @max_volume.setter
    def max_volume(self, max_volume: float):
        diameter, max_volume, max_pull = get_syringe_parameters(self.diameter, max_volume, self.max_pull)
        self.max_volume = max_volume

    @property
    def max_pull(self):
        return self._max_pull

    @max_pull.setter
    def max_pull(self, max_pull: float):
        diameter, max_volume, max_pull = get_syringe_parameters(self.diameter, self.max_volume, max_pull)
        self.max_pull = max_pull

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, volume):
        self._volume = volume

    @property
    def flow_rate(self):
        return self._flow_rate

    @flow_rate.setter
    def flow_rate(self, flow_rate):
        self._flow_rate = flow_rate

    @property
    def x(self):
        return self._x

    @flow_rate.setter
    def flow_rate(self, flow_rate):
        self._flow_rate = flow_rate

    def zero(self):
        pass
        self._x = 0
        self._volume = 0

    def run(self):
        pass

    def stop(self):
        pass
