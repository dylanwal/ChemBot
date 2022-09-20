import abc
import math
import enum

from chembot import configuration, logger, global_ids
import chembot.communication.base as communication
import chembot.utils.sig_figs as sig_figs
from chembot.errors import EquipmentError
from chembot.pump.flow_profile import PumpFlowProfile


def calc_pull(diameter: float, volume: float) -> float:
    return volume / (math.pi * (diameter / 2) ** 2)


def calc_volume(diameter: float, pull: float) -> float:
    return math.pi * (diameter / 2) ** 2 * pull


def calc_diameter(volume: float, pull: float) -> float:
    return 2 * math.sqrt(volume / (math.pi * pull))


class PumpState(enum.Enum):
    offline = 0
    standby = 1
    running_infuse = 2
    running_withdraw = 3
    stalled = 4
    error = 5


class PumpControlMethod(enum.Enum):
    flow_rate = 0
    pressure = 1


class Pump(abc.ABC):
    instances = []
    states = PumpState
    control_methods = PumpControlMethod

    def __init__(
            self,
            serial_line: communication.Communication,
            name: str = None,
            diameter: float | int = None,  # units: cm
            max_volume: float | int = None,  # units: ml
            max_pull: float | int = None,  # units: cm
            control_method: PumpControlMethod = PumpControlMethod.flow_rate,
    ):
        self._add_instance_()
        self.id_ = global_ids.get_id(self)

        self.serial_line = serial_line
        self.name = name if name is not None else f"pump_{len(self.instances)}"

        # setup everything
        self._diameter = None
        self._max_volume = None
        self._max_pull = None
        self._volume = 0
        self._flow_rate = 0
        self._pull = 0
        self._set_syringe_settings(diameter, max_volume, max_pull)
        self._state = PumpState.standby
        self._control_method = None
        self.control_method = control_method

        # additional attributes
        self._flow_profile = None

        logger.info(repr(self))

    def __repr__(self):
        text = f"Pump: {self.name} \n"
        text += f"current state: {self.state} \n"
        text += f"\tdiameter: {sig_figs.sig_figs(self.diameter, configuration.sig_fig_pump)} cm\n"
        text += f"\tmax_volume: {sig_figs.sig_figs(self.max_volume, configuration.sig_fig_pump)} ml\n"
        text += f"\tmax_pull: {sig_figs.sig_figs(self.max_pull, configuration.sig_fig_pump)} cm\n"
        text += f"\tvolume: {sig_figs.sig_figs(self.volume, configuration.sig_fig_pump)} ml\n"
        text += f"\tflow_rate: {sig_figs.sig_figs(self.flow_rate, configuration.sig_fig_pump)} ml/min\n"
        text += f"\tposition: {sig_figs.sig_figs(self.pull, configuration.sig_fig_pump)} ml \n"

        return text

    def _add_instance_(self):
        self.__class__.instances.append(self)
        self.syringe_count = 0
        self.syringe_setup = False

    def _set_syringe_settings(self,
                              diameter: float | int | None,
                              max_volume: float | int | None,
                              max_pull: float | int | None):

        if isinstance(diameter, (float, int)):
            self._check_diameter(diameter)
            if isinstance(max_volume, (float, int)):
                self._check_max_volume(max_volume)
                self._diameter = diameter
                self._max_volume = max_volume
                self._max_pull = calc_pull(diameter, max_volume)
                return

            elif isinstance(max_pull, (float, int)):
                self._check_max_pull(max_pull)
                self._diameter = diameter
                self._max_volume = calc_volume(diameter, max_pull)
                self._max_pull = max_pull
                return

        elif isinstance(max_volume, float):
            self._check_max_volume(max_volume)
            if isinstance(max_pull, float):
                self._check_max_pull(max_pull)
                self._diameter = calc_diameter(max_volume, max_pull)
                self._max_volume = max_volume
                self._max_pull = max_pull
                return

        raise EquipmentError(self, "Insufficient information provided for setup. 2 of 3 need: [diameter, max_volume, "
                                   "max_pull]")

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state: PumpState):
        self._state = state

    @property
    def diameter(self):
        return self._diameter

    @diameter.setter
    def diameter(self, diameter: float):
        self._check_diameter(diameter)
        max_volume = calc_volume(diameter, self.max_pull)
        self._check_max_volume(max_volume)
        self._max_volume = max_volume
        self._diameter = diameter

    def _check_diameter(self, diameter: float):
        if diameter <= 0 or not isinstance(diameter, (float, int)):
            raise EquipmentError(self, f"Diameter must be a positive float.\nGiven: {diameter}, {type(diameter)}")

    @property
    def max_volume(self):
        return self._max_volume

    @max_volume.setter
    def max_volume(self, max_volume: float | int):
        self._check_max_volume(max_volume)
        logger.warning("Changing 'max_volume' after initialization can cause mismatch with max_pull and diameter.")
        self._max_volume = max_volume

    def _check_max_volume(self, max_volume: float | int):
        if max_volume <= 0 or not isinstance(max_volume, (float, int)):
            raise EquipmentError(self,
                                 f"Max volume must be a positive float.\n Given: {max_volume}, {type(max_volume)}")

    @property
    def max_pull(self):
        return self._max_pull

    @max_pull.setter
    def max_pull(self, max_pull: float | int):
        self._check_max_pull(max_pull)
        max_volume = calc_volume(self.diameter, max_pull)
        self._check_max_volume(max_volume)
        self._max_volume = max_volume
        self._max_pull = max_pull

    def _check_max_pull(self, max_pull: float | int):
        if max_pull <= 0 or not isinstance(max_pull, (float, int)):
            raise EquipmentError(self, f"Max pull must be a positive float.\n Given: {max_pull}, {type(max_pull)}")

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, volume: float):
        self._check_volume(volume)
        pull = calc_pull(self.diameter, volume)
        self._check_pull(pull)
        self._pull = pull
        self._volume = volume

    def _check_volume(self, volume: int | float):
        if not isinstance(volume, (int, float)):
            raise EquipmentError(self, f"'volume' must be an int or float. \n given: {type(volume)}")

        if 0 > volume or self.max_volume < volume:
            raise EquipmentError(self, f"Requested 'volume' is outside the acceptable range. \n"
                                       f"range: [0, {self.max_volume}], requested: {volume}")

    @property
    def pull(self):
        return self._pull

    @pull.setter
    def pull(self, pull: int | float):
        self._check_pull(pull)
        volume = calc_volume(self.diameter, pull)
        self._check_volume(volume)
        self._volume = volume
        self._pull = pull

    def _check_pull(self, pull: int | float):
        if not isinstance(pull, (int, float)):
            raise EquipmentError(self, f"'pull' must be an int or float. \n given: {type(pull)}")

        if pull < 0 or pull > self.max_pull:
            raise EquipmentError(self, f"Requested 'pull' is outside the acceptable range. \n"
                                       f"range: [0, {self.max_pull}], requested: {pull}")

    @property
    def flow_rate(self):
        return self._flow_rate

    def empty(self):
        """"""
        pass
        self._pull = 0
        self._volume = 0

    def fill(self):
        pass
        self._pull = self.max_pull
        self._volume = self._max_volume

    def setup_flow(self, flow_profile: PumpFlowProfile):
        pass

    def run(self):
        pass

    def stop(self):
        pass
