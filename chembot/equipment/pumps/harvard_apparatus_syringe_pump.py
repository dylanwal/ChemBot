from __future__ import annotations

import enum
import logging
import time
from datetime import timedelta

import serial
from unitpy import Quantity, Unit

from chembot.configuration import config
from chembot.equipment.pumps.syringe_pump import SyringePump, SyringePumpStatus
from chembot.equipment.pumps.syringes import Syringe
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


class CommandError(Exception):
    """
    Command errors are displayed when the command is unrecognized, or entered in while the pump is in the wrong mode,
    or the state of the pump keeps the command from executing
    """


class ArgumentError(Exception):
    """
    Argument errors are displayed when a command argument is unrecognized or out of range.
    The argument in question will be displayed except in the case of missing arguments.
    """

#######################################################################################################################
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
#######################################################################################################################


class HarvardPumpStatusDirection(enum.Enum):
    infuse = "i"
    withdraw = "w"


class HarvardPumpStatusMessage:
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
    def parse_message(cls, message: str) -> HarvardPumpStatusMessage:
        # parse reply
        # format: '\n0 0 0 w..TI.\r\n:'
        message = message \
            .replace("\n", "") \
            .split(" ")

        status = cls()
        # integer terms
        status.flow_rate = int(message[0]) * Unit("fL/s")  # Yes, it is femtoliters per second
        status.time_ = int(message[1]) * Unit("ms")
        status.displaced_volume = int(message[2]) * Unit("fL")  # Yes, it is femtoliters

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
    """
    for USB only; assumes echo is off.

    pump sends reply when target reached.
    It does NOT send reply when stalled.

    """
    ramp_object = RampFlowRate
    poll_gap = 5  # sec

    def __init__(self,
                 name: str,
                 syringe: Syringe,
                 port: str,
                 max_pull: Quantity = None,
                 # control_method: PumpControlMethod = PumpControlMethod.flow_rate,
                 ):
        super().__init__(name, syringe, max_pull)

        # serial dropped directly here because USB is one-one and the pump sends messages without prompt.
        Serial.available_port(port)
        self.serial = serial.Serial(port=port, timeout=0.4)
        self.serial.flushInput()
        self.serial.flushOutput()

        self._next_poll_time = 0

    def _check_pump_reply(self, message: str) -> str:
        # check for target reached  'T:' or 'T*'
        if "T" in message[0]:
            self.pump_state.state = SyringePumpStatus.TARGET_REACHED
            self.state = self.states.STANDBY
            if message[1] == HarvardPumpStatus.STALLED.value:
                self._send_and_receive_message("stop")
            return message[2:]

        # check general status ':', '*', '>', '<'
        if message[0] == HarvardPumpStatus.STALLED.value:
            self.state = self.states.STANDBY
            self._send_and_receive_message("stop")
        status = message[0]
        for option in HarvardPumpStatus:
            if status == option.value:
                self.pump_state.state = map_status[option]
                break
        else:
            logger.error(f"message:{message}")
            raise ValueError("Unrecognized status from Harvard Pump reply.")

    def _send_and_receive_message(self,
                                  prompt: str,
                                  time_out: float = 0.2,
                                  retries: int = 3
                                  ) -> str:
        logger.debug(f"{self.name} | send: {prompt}")
        for i in range(retries):
            # '@' turns off GUI updates for faster communication rates
            self.serial.write(("@" + prompt + "\r").encode(config.encoding))

            try:
                return self._read(time_out)
            except Exception as e:
                if i < retries-1:
                    self.serial.flushInput()
                    continue
                raise e

    def _read(self, time_out: float | int = 0.2, retries: int = 3) -> str:
        """

        Parameters
        ----------
        time_out
        retries

        Notes
        -----
        message format: <lf><prompt>
            - first read_until always returns "\n"
            - the second read has data

        """
        self.serial.timeout = time_out
        for i in range(retries):
            try:
                reply = self.serial.read_until().decode(config.encoding)
                if reply == "\n" or reply == "\r\n":
                    reply = self.serial.read_until().decode(config.encoding)
                logger.debug(f"{self.name} | reply: " + reply.replace("\n", r"\n").replace("\r", r"\r"))
                if "Argument error" in reply:
                    raise ArgumentError(reply)
                if "Command error" in reply:
                    raise CommandError(reply)
                return reply

            except Exception as e:
                if i < retries-1 and (e is not ArgumentError or e is not CommandError):
                    continue
                if "reply" in locals():
                    print("reply:", reply)  # noqa
                if self.serial.in_waiting > 0:
                    print("in buffer:", self.serial.read_all())
                raise e

    def _activate(self):
        # set syringe settings
        self._send_and_receive_message("NVRAM off")  # turn off writes of rate to memory -> faster communication
        self._write_diameter(self.syringe.diameter)
        self.write_empty()
        self.write_force(self.syringe.force)
        super()._activate()

    def _deactivate(self):
        self._stop()
        self.serial.close()

    def _poll_status(self):
        if self.serial.in_waiting:
            self._read()
            logger.info(f"{self.name} | Pump finished addition or stalled.")
            if self.pump_state.state is SyringePumpStatus.STALLED and self.state is self.states.RUNNING:
                if not self.pump_state.volume_in_syringe.is_close(0 * Unit.ml, abs_tol=0.01 * Unit.ml):
                    # ignore stall if its close to zero volume in syringe
                    logger.error(config.log_formatter(self, self.name, "Error stalled detected!!!"))
                self.write_stop()

        if self.state is self.states.RUNNING and time.time() > self._next_poll_time:
            self.read_pump_status()
            self._next_poll_time = time.time() + self.poll_gap

    ## actions ################################################################################################# noqa
    def _stop(self):
        reply = self._send_and_receive_message("stop")
        self._check_pump_reply(reply)

    def _write_run_infuse(self):
        """
        run infuse
        """
        reply = self._send_and_receive_message('irun')
        self._check_pump_reply(reply)
        self.state = self.states.RUNNING
        self.pump_state.state = self.pump_states.INFUSE
        self.pump_state.running_time = 0 * Unit.s
        self.pump_state.volume_displace = 0 * self.syringe.volume.unit

    def _write_run_withdraw(self):
        """
        run withdraw
        """
        reply = self._send_and_receive_message(f'wrun')
        self._check_pump_reply(reply)
        self.state = self.states.RUNNING
        self.pump_state.state = self.pump_states.WITHDRAW
        self.pump_state.running_time = 0 * Unit.s
        self.pump_state.volume_displace = 0 * self.syringe.volume.unit

    def _write_run_withdraw2(self):
        """
        run withdraw
        """
        reply = self._send_and_receive_message(f'run')
        self._check_pump_reply(reply)
        if self.pump_state.state != HarvardPumpStatus.WITHDRAW:
            self._flip_direction()

        self.state = self.states.RUNNING
        self.pump_state.state = self.pump_states.WITHDRAW
        self.pump_state.running_time = 0 * Unit.s
        self.pump_state.volume_displace = 0 * self.syringe.volume.unit

    def _flip_direction(self):
        reply = self._send_and_receive_message(f'rrun')

    def write_infuse(self, volume: Quantity, flow_rate: Quantity, ignore_syringe_error: bool = False):
        """
        infuse

        Parameters
        ----------
        volume:
            volume to be infused
        flow_rate:
            flow rate
        ignore_syringe_error:
            True: don't throw an error if the pump stops due to stall
            False: will throw an error
        """
        # validation of inputs
        validate_quantity(volume, Syringe.volume_dimensionality, "volume", True)
        validate_quantity(flow_rate, Syringe.flow_rate_dimensionality, "flow_rate", True)
        if not ignore_syringe_error and \
                self.pump_state.within_max_pull(self.compute_pull(self.syringe.diameter, volume)):
            raise ValueError("Stall expected as pull too large pull. Lower volume infused or set ignore_stall=False")

        # setup pump
        self._write_infuse_volume_clear()
        self._write_infuse_time_clear()
        self._write_target_time_clear()
        self._write_target_volume(volume)
        self.write_infusion_rate(flow_rate)
        self.write_force(100)  # TODO: improve turn down after some time
        # self._write_target_time(self.compute_run_time(volume, flow_rate).to_timedelta())

        # run
        self._write_run_infuse()

        # update status
        self.pump_state.flow_rate = flow_rate
        self.pump_state.target_volume = volume
        self.pump_state.end_time = self.compute_run_time(volume, flow_rate)

    def write_withdraw(self, volume: Quantity, flow_rate: Quantity):
        """
        withdraw

        Parameters
        ----------
        volume:
            volume
        flow_rate:
            flow rate
        """
        # validation of inputs
        validate_quantity(volume, Syringe.volume_dimensionality, "volume", True)
        validate_quantity(flow_rate, Syringe.flow_rate_dimensionality, "flow_rate", True)
        if self.pump_state.within_max_pull(self.compute_pull(self.syringe.diameter, volume)):
            raise ValueError("Too much withdraw volume requested. Lower volume withdraw")

        # setup pump
        self._write_withdraw_volume_clear()
        self._write_withdrawn_time_clear()
        self._write_target_time_clear()
        self._write_target_volume(volume)
        self.write_withdraw_rate(flow_rate)
        self.write_force(100)
        # self._write_target_time(self.compute_run_time(volume, flow_rate).to_timedelta())

        # run
        self._write_run_withdraw() #########################

        # update status
        self.pump_state.flow_rate = flow_rate
        self.pump_state.target_volume = volume
        self.pump_state.end_time = self.compute_run_time(volume, flow_rate)

    def write_empty(self, flow_rate: Quantity = None):
        """ empty syringe """
        if flow_rate is None:
            flow_rate = self.syringe.default_flow_rate
        self.write_infuse(self.syringe.volume, flow_rate, ignore_syringe_error=True)

        # run till it stalls (with safe timeout)
        self.pump_state.volume_in_syringe = 0 * self.syringe.volume.unit
        time_out = (self.syringe.volume / self.syringe.default_flow_rate).to("s").value + 10  # seconds
        time_stop = time.time() + time_out
        while time.time() < time_stop:
            self.read_pump_status()
            if self.pump_state.state is SyringePumpStatus.STALLED:
                break
            time.sleep(0.1)

        if self.pump_state.state is not SyringePumpStatus.STALLED:
            raise ValueError("Pump not successful at emptying.")

        self.pump_state.volume_in_syringe = 0 * self.syringe.volume.unit
        self._stop()  # to stop tone

    def write_refill(self, flow_rate: Quantity = None):
        """ refill syringe to max volume """
        if flow_rate is None:
            flow_rate = self.syringe.default_flow_rate

        volume = self.syringe.volume - self.pump_state.volume_in_syringe
        self.write_withdraw(volume, flow_rate)

    # def _write_run(self):
    #     _ = self._send_and_receive_message('run')

    ## settings ################################################################################################# noqa
    # def _write_echo_off(self):
    #     """ sets echo state to off """
    #     _ = self._send_and_receive_message('echo off')

    def read_version(self) -> str:
        """
        Displays the short version string.
        """
        reply = self._send_and_receive_message('ver')

        # parse reply
        # format b'\nPHD ULTRA 3.0.5\r\n:'
        reply = reply[:-3].replace("\n", "").replace("\r", "")

        return reply

    def read_version_long(self) -> HarvardPumpVersion:
        """
        Displays the full version string.
        """
        reply = self._send_and_receive_message('version')
        return HarvardPumpVersion.parse_message(reply)

    def read_pump_status(self) -> HarvardPumpStatusMessage:
        """
        Displays the raw status for use with a controlling computer.
        """
        reply = self._send_and_receive_message('status')
        reply2 = self._read()
        if reply2[0].isdigit():  # old pumps flip order
            reply, reply2 = reply2, reply
        self._check_pump_reply(reply2)
        try:
            status = HarvardPumpStatusMessage.parse_message(reply)
            return status
        except Exception:
            logger.warning("invalid status received.")
        # self.pump_state.volume_displace = status.displaced_volume
        # self.pump_state.flow_rate = status.flow_rate
        # self.pump_state.running_time = status.time_

    def read_force(self) -> int:
        """
        Displays the infusion force level in percent.
        """
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
            range: [30:1:100]
        """
        # input validation
        force = int(force)
        if not (1 <= force <= 100):
            raise ValueError("force outside range [30, 100]")

        _ = self._send_and_receive_message(f'force {force:03}')

    def _read_diameter(self) -> Quantity:
        """
        Displays the syringe diameter
        """
        reply = self._send_and_receive_message(f'diameter')

        # parse reply
        # format: '\n9.5250 mm\r\n:'
        reply = reply[:-2] \
            .replace("\n", "")\
            .replace("\r", "")

        return Quantity(reply)

    def write_syringe(self, syringe: Syringe):
        """
        set syringe
        """
        self._write_diameter(syringe.diameter)
        super().write_syringe(syringe)

    def _write_diameter(self, diameter: Quantity):
        # input validation
        diameter = diameter.to("mm")
        if diameter.value > 45:
            raise ValueError("diameter outside range [0, 45 mm]")

        reply = self._send_and_receive_message(f'diameter {diameter.v:2.4f}')
        self._check_pump_reply(reply)

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

    ## flow rate ################################################################################################# noqa
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

    def read_infusion_rate_command(self) -> Quantity:
        """
        pings pump for infusion rate
        """
        reply = self._send_and_receive_message(f'irate')

        # parse reply
        # format: '\n15.3477 ml/min\r\n:'
        reply = reply.replace("\n", "").replace("\r", "")
        return Quantity(reply)

    def write_infusion_rate(self, flow_rate: Quantity):
        flow_rate = set_flow_rate_range(flow_rate)
        _ = self._send_and_receive_message(f'irate {flow_rate.v:2.4f} {flow_rate.unit.abbr}')
        self.pump_state.flow_rate = flow_rate

    def read_withdraw_rate(self) -> Quantity:
        """
        pings pump for infusion rate
        """
        reply = self._send_and_receive_message(f'wrate')

        # parse reply
        # format: '\n15.3477 ml/min\r\n:'
        reply = reply.replace("\n", "").replace("\r", "")
        return Quantity(reply)

    def write_withdraw_rate(self, flow_rate: Quantity):
        flow_rate = set_flow_rate_range(flow_rate)
        _ = self._send_and_receive_message(f'wrate {flow_rate.v:2.4f} {flow_rate.unit.abbr}')
        self.pump_state.flow_rate = flow_rate

    ## volume ################################################################################################### noqa
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
        volume = set_volume_range(volume)
        _ = self._send_and_receive_message(f'tvolume {volume.v:2.4f} {volume.unit.abbr}')

    def _write_target_volume_clear(self):
        _ = self._send_and_receive_message(f'ctvolume')

    def _write_infuse_volume_clear(self):
        _ = self._send_and_receive_message(f'civolume')

    def _write_withdraw_volume_clear(self):
        _ = self._send_and_receive_message(f'cwvolume')

    ## time #################################################################################################### noqa
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

    def _write_target_time_clear(self):
        _ = self._send_and_receive_message(f'cttime')

    def _write_withdrawn_time_clear(self):
        _ = self._send_and_receive_message(f'cwtime')

    def _write_infuse_time_clear(self):
        _ = self._send_and_receive_message(f'citime')

    def _write_target_clear(self):
        self._write_target_time_clear()
        self._write_target_volume_clear()

    ## ramp #################################################################################################### noqa
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

        # run
        self._write_run_infuse()

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

        # run
        self._write_run_withdraw()
