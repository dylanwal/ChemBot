from __future__ import annotations

import enum
import logging
from datetime import timedelta

from unitpy import Quantity, Unit

from chembot.configuration import config
from chembot.equipment.pumps.syringe_pump import SyringePump, PumpControlMethod, SyringePumpStatus
from chembot.equipment.pumps.syringes import Syringe
from chembot.rabbitmq.messages import RabbitMessageAction
from chembot.communication.serial_ import Serial
from chembot.utils.unit_validation import validate_quantity

logger = logging.getLogger(config.root_logger_name + ".pump")


class HarvardPumpStatus(enum.Enum):
    STANDBY = ":"
    INFUSE = ">"
    WITHDRAW = "<"
    STALLED = "*"
    TARGET_REACHED = "T"


map_status = {
    HarvardPumpStatus.STANDBY: SyringePumpStatus.STANDBY,
    HarvardPumpStatus.INFUSE: SyringePumpStatus.INFUSE,
    HarvardPumpStatus.WITHDRAW: SyringePumpStatus.WITHDRAW,
    HarvardPumpStatus.STALLED: SyringePumpStatus.STALLED,
    HarvardPumpStatus.TARGET_REACHED: SyringePumpStatus.TARGET_REACHED
}


def check_status(message: str) -> SyringePumpStatus:
    if "T" in message:
        return SyringePumpStatus.TARGET_REACHED

    status = message[-1]
    for option in HarvardPumpStatus:
        if status == option.value:
            return map_status[option]

    raise ValueError("Unrecognized status from Harvard Pump reply.")


def check_for_error(message: str):
    """ '\nArgument error: [on]\r\n   Unknown argument\r\n:' """
    if "Argument error" in message:
        raise ArgumentError(message)
    if "Command error" in message:
        raise CommandError(message)


class CommandError(Exception):
    """
    Command errors are displayed when the command is unrecognized, entered in the wrong mode,
    or the state of the pump keeps the command from executing
    """


class ArgumentError(Exception):
    """
    Argument errors are displayed when a command argument is unrecognized or out of range.
    The argument in question will be displayed except in the case of missing arguments.
    """

#######################################################################################################################


class HarvardPumpVersion:
    def __init__(self,
                 firmware: str = None,
                 address: int = None,
                 serial_number: str = None,
                 ):
        self.firmware = firmware
        self.address = address
        self.serial_number = serial_number

    @classmethod
    def parse_message(cls, message: str) -> HarvardPumpVersion:
        # format: '\nFirmware:      v3.0.5\r\nPump address:  0\r\nSerial number: D401460\r\n:'
        message = message[:-3] \
            .replace("\n", "") \
            .replace("Firmware", "firmware") \
            .replace("Pump address", "address") \
            .replace("Serial number", "serial_number") \
            .replace(" ", "") \
            .split("\r")

        version = cls()
        version.firmware = message[0].split(":")[1]
        version.firmware = int(message[1].split(":")[1])
        version.firmware = message[2].split(":")[1]

        return version

#######################################################################################################################


class HarvardPumpStatusDirection(enum.Enum):
    infuse = "i"
    withdraw = "w"


class HarvardPumpStatus:
    directions = HarvardPumpStatusDirection

    def __init__(self,
                 flow_rate: Quantity = None,
                 time_: Quantity = None,
                 displaced_volume: Quantity = None,
                 motor_direction: HarvardPumpStatusDirection = None,
                 running: bool = None,
                 limit_switch_hit_infuse: bool | None = None,
                 limit_switch_hit_withdraw: bool | None = None,
                 stalled: bool = None,
                 triggered: bool = None,
                 port_state: HarvardPumpStatusDirection = None,
                 target_reached: bool = None
                 ):
        self.flow_rate = flow_rate
        self.time_ = time_
        self.displaced_volume = displaced_volume
        self.motor_direction = motor_direction
        self.running = running
        self.limit_switch_hit_infuse = limit_switch_hit_infuse
        self.limit_switch_hit_withdraw = limit_switch_hit_withdraw
        self.stalled = stalled
        self.triggered = triggered
        self.port_state = port_state
        self.target_reached = target_reached

    @classmethod
    def parse_message(cls, message: str) -> HarvardPumpStatus:
        # parse reply
        # format: '\n0 0 0 w..TI.\r\n:'
        message = message[:-3] \
            .replace("\n", "") \
            .split(" ")

        status = cls()
        # integer terms
        status.flow_rate = int(message[0]) * Unit("fL")
        status.time_ = int(message[1]) * Unit("ms")
        status.displaced_volume = int(message[2]) * Unit("fL")

        flag_field = message[3]
        # first term
        if flag_field[0] == "i":
            status.motor_direction = HarvardPumpStatusDirection.infuse
            status.running = False
        elif flag_field[0] == "I":
            status.motor_direction = HarvardPumpStatusDirection.infuse
            status.running = True
        elif flag_field[0] == "w":
            status.motor_direction = HarvardPumpStatusDirection.withdraw
            status.running = False
        else:  # "W"
            status.motor_direction = HarvardPumpStatusDirection.withdraw
            status.running = True

        # second term
        if flag_field[1] == "i" or flag_field[1] == "I":
            status.limit_switch_hit_infuse = True
        elif flag_field[1] == "w" or flag_field[1] == "W":
            status.limit_switch_hit_withdraw = True
        # '.' does not have limit switch and is left as None

        # third term
        if flag_field[2] == "S":
            status.stalled = True
        else:  # '.'
            status.stalled = False

        # forth term
        if flag_field[3] == "T":
            status.triggered = True
        else:  # '.'
            status.triggered = False

        # fifth term
        if flag_field[4] == "i" or flag_field[4] == "I":
            status.port_state = HarvardPumpStatusDirection.infuse
        else:  # 'w' or 'W'
            status.port_state = HarvardPumpStatusDirection.withdraw

        # sixth term
        if flag_field[5] == "T":
            status.target_reached = True
        else:  # '.'
            status.target_reached = False

        return status


#######################################################################################################################

class RampFlowRate:
    def __init__(self,
                 flow_rate_start: Quantity = None,
                 flow_rate_end: Quantity = None,
                 time_ramp: timedelta = None,
                 ):
        self._flow_rate_start = None
        self._flow_rate_end = None

        self.flow_rate_start = flow_rate_start
        self.flow_rate_end = flow_rate_end
        self.time_ramp = time_ramp

    @property
    def flow_rate_start(self) -> Quantity:
        return self._flow_rate_start

    @flow_rate_start.setter
    def flow_rate_start(self, flow_rate: Quantity):
        if flow_rate is None:
            return
        validate_quantity(flow_rate, Syringe.flow_rate_dimensionality, 'Ramp.flow_rate_start', True)
        self._flow_rate_start = flow_rate

    @property
    def flow_rate_end(self) -> Quantity:
        return self._flow_rate_end

    @flow_rate_end.setter
    def flow_rate_end(self, flow_rate: Quantity):
        if flow_rate is None:
            return
        validate_quantity(flow_rate, Syringe.flow_rate_dimensionality, 'Ramp.flow_rate_end', True)
        self._flow_rate_end = flow_rate

    def as_string(self) -> str:
        flow_rate_start = set_flow_rate_range(self.flow_rate_start)
        flow_rate_end = set_flow_rate_range(self.flow_rate_end)
        return f"{flow_rate_start.v} {flow_rate_start.unit.abbr} {flow_rate_end.v} {flow_rate_end.unit.abbr} " \
               f"{self.time_ramp.total_seconds()}"

#######################################################################################################################
#######################################################################################################################


def set_flow_rate_range(flow_rate: Quantity) -> Quantity:
    # change units for correct string formatting
    if flow_rate > 0.1 * Unit("ml/min"):
        return flow_rate.to("ml/min")
    elif flow_rate > 0.1 * Unit("ul/min"):
        return flow_rate.to("ul/min")
    else:
        return flow_rate.to("nl/min")


def set_volume_range(volume: Quantity) -> Quantity:
    # change units for correct string formatting
    if volume > 0.1 * Unit("ml"):
        return volume.to("ml")
    elif volume > 0.1 * Unit("ul"):
        return volume.to("ul")
    else:
        return volume.to("nl")


def process_time(time_str: str) -> timedelta:
    h, m, s = time_str.split(':')
    return timedelta(hours=int(h), minutes=int(m), seconds=int(s))


class SyringePumpHarvard(SyringePump):
    """ for USB only; assumes echo is off. """
    ramp_object = RampFlowRate
    pump_status = HarvardPumpStatus
    status_message = HarvardPumpStatus

    def __init__(self,
                 name: str,
                 syringe: Syringe,
                 communication: str,
                 max_pull: Quantity = None,
                 max_pull_rate: Quantity = None,
                 control_method: PumpControlMethod = PumpControlMethod.flow_rate,
                 ):
        super().__init__(name, syringe, max_pull, max_pull_rate, control_method)
        self.communication = communication

    def _send_and_receive_message(self, prompt: str) -> str:
        message = RabbitMessageAction(self.communication, self.name, Serial.write_plus_read_all_buffer,
                                      {"message": prompt + "\r"})
        reply = self.rabbit.send_and_consume(message).value

        # check for error
        check_for_error(reply)
        self.pump_status = check_status(reply[:-2])

        return reply[:-2]  # remove status

    def _activate(self):
        # ping communication to ensure it is alive
        message = RabbitMessageAction(self.communication, self.name, "read_name")
        self.rabbit.send_and_consume(message, error_out=True)

        # set syringe settings
        self._write_diameter(self.syringe.diameter)

    def _stop(self):
        _ = self._send_and_receive_message("stop")

    def _poll_status(self):
        status = self.read_pump_status()
        self._volume = None
        self._volume_displace = None
        self._flow_rate = None
        self._target_volume = None
        self._running_time = None
        self._end_time = None
        self._pull = None

    def _write_infuse(self, volume: Quantity, flow_rate: Quantity):
        self._write_target_time_clear()
        self.write_infusion_rate(flow_rate)
        self._write_target_volume(volume)
        self.write_run_infuse()

    def _write_withdraw(self, volume: Quantity, flow_rate: Quantity):
        self._write_target_time_clear()
        self.write_withdraw_rate(flow_rate)
        self._write_target_volume(volume)
        self.write_run_withdraw()

    def write_run_infuse(self):
        _ = self._send_and_receive_message(f'irun')
        self.state = self.states.RUNNING
        self.pump_status = self.pump_states.INFUSE
        #TODO: set look for end message

    def write_run_withdraw(self):
        _ = self._send_and_receive_message(f'wrun')
        self.state = self.states.RUNNING
        self.pump_status = self.pump_states.INFUSE
        #TODO: set look for end message

    # def _write_run(self):
    #     _ = self._send_and_receive_message('run')

    # def _write_echo_off(self):
    #     """ sets echo state to off """
    #     _ = self._send_and_receive_message('echo off')

    def read_version(self) -> str:
        """ Displays the short version string. """
        reply = self._send_and_receive_message('ver')

        # parse reply
        # format b'\nPHD ULTRA 3.0.5\r\n:'
        reply = reply[:-3].replace("\n", "").replace("\r", "")

        return reply

    def read_version_long(self) -> HarvardPumpVersion:
        """ Displays the full version string. """
        reply = self._send_and_receive_message('version')
        return HarvardPumpVersion.parse_message(reply)

    def read_pump_status(self) -> HarvardPumpStatus:
        """ Displays the raw status for use with a controlling computer. """
        reply = self._send_and_receive_message('status')
        return HarvardPumpStatus.parse_message(reply)

    def read_force(self) -> int:
        """ Displays the infusion force level in percent. """
        reply = self._send_and_receive_message('force')

        # parse reply
        # format: '\n100%\r\n:'
        reply = reply[:-2] \
            .replace("\n", "")\
            .replace("%", "")
        return int(reply)

    def write_force(self, force: int):
        """
        Sets the infusion force level in percent.

        Parameters
        ----------
        force:
            force
            range: [1, ..., 100]
        """
        # input validation
        force = int(force)
        if not (1 <= force <= 100):
            raise ValueError("force outside range [0, 100]")

        _ = self._send_and_receive_message(f'force {force:03}')

    def _read_diameter(self) -> Quantity:
        """ Displays the syringe diameter """
        reply = self._send_and_receive_message(f'diameter')

        # parse reply
        # format: '\n9.5250 mm\r\n:'
        reply = reply[:-2] \
            .replace("\n", "")\
            .replace("\r", "")

        return Quantity(reply)

    def write_syringe(self, syringe: Syringe):
        """ set syringe """
        self._write_diameter(syringe.diameter)
        super().write_syringe(syringe)

    def _write_diameter(self, diameter: Quantity):
        # input validation
        diameter = diameter.to("mm")
        if diameter.value > 45:
            raise ValueError("diameter outside range [0, 45 mm]")

        _ = self._send_and_receive_message(f'diameter {diameter.v:2.4f}')

    # def _read_gang(self) -> int:
    #     """ Displays the syringe count """
    #     reply = self._send_and_receive_message(f'gang')
    #
    #     # parse reply
    #     # format: '\n1 syringes\r\n:'
    #     return int(reply[1])
    #
    # def _write_gang(self, gang: int):
    #     """ the syringe count -- unsure how it effects flow rate calculations on the pump """
    #     # input validation
    #     if 0 < gang < 3:
    #         raise ValueError("diameter outside range [0, 2]")
    #
    #     _ = self._send_and_receive_message(f'gang {gang}')

    def _read_max_flow_rate(self) -> Quantity:
        """ get max flow rate accepted by pump (dependent on set syringe) """
        reply = self._send_and_receive_message(f'irate lim')

        # parse reply
        # format: '\n14.7792 nl/min to 15.3477 ml/min\r\n:'
        reply = reply.replace("\n", "").replace("\r", "")
        index = reply.index("o")
        return Quantity(reply[index+2:])

    def _read_min_flow_rate(self) -> Quantity:
        """ get min flow rate accepted by pump (dependent on set syringe) """
        reply = self._send_and_receive_message(f'irate lim')

        # parse reply
        # format: '\n14.7792 nl/min to 15.3477 ml/min\r\n:'
        reply = reply.replace("\n", "")
        index = reply.index("t")
        return Quantity(reply[:index])

    def read_infusion_rate(self) -> Quantity:
        """ display the infusion rate """
        reply = self._send_and_receive_message(f'irate')

        # parse reply
        # format: '\n15.3477 ml/min\r\n:'
        reply = reply.replace("\n", "").replace("\r", "")
        return Quantity(reply)

    def write_infusion_rate(self, flow_rate: Quantity):
        flow_rate = set_flow_rate_range(flow_rate)
        _ = self._send_and_receive_message(f'irate {flow_rate.v:2.4f} {flow_rate.unit.abbr}')

    def read_withdraw_rate(self) -> Quantity:
        """ display the withdrawal rate """
        reply = self._send_and_receive_message(f'wrate')

        # parse reply
        # format: '\n15.3477 ml/min\r\n:'
        reply = reply.replace("\n", "").replace("\r", "")
        return Quantity(reply)

    def write_withdraw_rate(self, flow_rate: Quantity):
        flow_rate = set_flow_rate_range(flow_rate)
        _ = self._send_and_receive_message(f'wrate {flow_rate.v:2.4f} {flow_rate.unit.abbr}')

    def _read_infuse_volume(self) -> Quantity:
        reply = self._send_and_receive_message(f'ivolume')

        # parse reply
        # format: b'\n0 ul\r\n:'
        reply = reply.replace("\n", "").replace("\r", "")
        return Quantity(reply)

    def _read_withdraw_volume(self) -> Quantity:
        reply = self._send_and_receive_message(f'wvolume')

        # parse reply
        # format: b'\n0 ul\r\n:'
        reply = reply.replace("\n", "").replace("\r", "")
        return Quantity(reply)

    def _read_target_volume(self) -> Quantity | None:
        reply = self._send_and_receive_message(f'tvolume')

        # parse reply
        # format: b'\n0 ul\r\n:'
        if "Target" in reply:  # 'target volume not set' returns None
            return None

        reply = reply.replace("\n", "").replace("\r", "")
        return Quantity(reply)

    def _write_target_volume(self, volume: Quantity):
        volume = set_flow_rate_range(volume)
        _ = self._send_and_receive_message(f'tvolume {volume.v:2.4f} {volume.unit.abbr}')

    def _read_infuse_time(self) -> timedelta:
        reply = self._send_and_receive_message(f'itime')

        # parse reply
        # format: b'\n0 seconds\r\n:'
        reply = reply.replace("\n", "").replace("\r", "").replace(" ", "")
        if "seconds" in reply:
            reply = reply.replace("seconds", "")
            return timedelta(seconds=int(reply))

        # format: '\n00:01:40\r\n:'
        return process_time(reply)

    def _read_withdraw_time(self) -> timedelta:
        reply = self._send_and_receive_message(f'wtime')

        # parse reply
        reply = reply.replace("\n", "").replace("\r", "").replace(" ", "")
        if "seconds" in reply:
            reply = reply.replace("seconds", "")
            return timedelta(seconds=int(reply))

        # format: '\n00:01:40\r\n:'
        return process_time(reply)

    def _read_target_time(self) -> timedelta | None:
        reply = self._send_and_receive_message(f'ttime')

        # parse reply
        # format: '\n0 ul\r\n:'
        if "Target" in reply:  # 'target volume not set' returns None
            return None

        reply = reply.replace("\n", "").replace("\r", "").replace(" ", "")
        if "seconds" in reply:
            reply = reply.replace("seconds", "")
            return timedelta(seconds=int(reply))

        # format: '\n00:01:40\r\n:'
        return process_time(reply)

    def _write_target_time(self, time_: timedelta):
        sec = time_.total_seconds()
        hours = int(sec // 3600)
        sec -= (hours * 3600)
        minutes = int(sec // 60)
        sec -= (minutes * 60)
        sec = int(sec)
        _ = self._send_and_receive_message(f'ttime {hours:02}:{minutes:02}:{sec:02}')

    def _read_infuse_ramp(self) -> RampFlowRate | None:
        reply = self._send_and_receive_message(f'iramp')

        # parse reply
        # format: '\n15.3477 ml/min to 15.3477 ml/min in 80 seconds\r\n:'
        if "Ramp" in reply:  # RAMP not set up.
            return None

        reply = reply.replace("\n", "")
        reply = reply.strip(" to ")
        flow_rate_start = Quantity(reply[0])
        reply = reply[2].split(" in ")
        flow_rate_end = Quantity(reply[0])
        reply = reply[1].replace(" seconds\r", "")
        time_ = timedelta(int(reply))

        return RampFlowRate(flow_rate_start, flow_rate_end, time_)

    def write_infuse_ramp(self, ramp: RampFlowRate):
        _ = self._send_and_receive_message(f'iramp {ramp.as_string()}')

    def _read_withdraw_ramp(self) -> RampFlowRate | None:
        reply = self._send_and_receive_message(f'wramp')

        # parse reply
        # format: '\n15.3477 ml/min to 15.3477 ml/min in 80 seconds\r\n:'
        if "Ramp" in reply:  # RAMP not set up.
            return None

        reply = reply.replace("\n", "")
        reply = reply.strip(" to ")
        flow_rate_start = Quantity(reply[0])
        reply = reply[2].split(" in ")
        flow_rate_end = Quantity(reply[0])
        reply = reply[1].replace(" seconds\r", "")
        time_ = timedelta(int(reply))

        return RampFlowRate(flow_rate_start, flow_rate_end, time_)

    def write_withdraw_ramp(self, ramp: RampFlowRate):
        _ = self._send_and_receive_message(f'wramp {ramp.as_string()}')

    def _write_target_time_clear(self):
        _ = self._send_and_receive_message(f'cttime')

    def _write_target_volume_clear(self):
        _ = self._send_and_receive_message(f'ctvolume')

    def _write_target_clear(self):
        self._write_target_time_clear()
        self._write_target_volume_clear()
