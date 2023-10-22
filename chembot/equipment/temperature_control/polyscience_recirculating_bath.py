"""PolyScience Circulating Bath"""
import logging

from serial import Serial
from unitpy import Quantity, Unit

from chembot.configuration import config
from chembot.equipment.temperature_control.base import TempControl

logger = logging.getLogger(config.root_logger_name + ".lights")


class PolyScienceBath:
    def __init__(self,
                 comport: str,
                 temp_limits: tuple[Quantity, Quantity] = (5 * Unit.degC, 60 * Unit.degC),
                 encoding: str = "UTF8"
                 ):
        self.serial = Serial(comport, timeout=1)
        self.encoding = encoding

        self._activate()
        self._temp_limits = None
        self.temp_limits = temp_limits

    def _activate(self):
        self.serial.flushInput()
        self.serial.flushOutput()
        self._write_echo(False)

    def deactivate(self):
        self.write_off()
        self.serial.close()

    def _read(self, expected_reply: str):
        reply = self.serial.read(len(expected_reply))
        try:
            if reply.decode() != expected_reply or self.serial.in_waiting:
                raise
        except Exception as e:
            logger.error(f"reply:{reply}")
            if self.serial.in_waiting:
                logger.error(f"reply2:{self.serial.read(self.serial.in_waiting)}")
            raise e

    def _write(self, message: str):
        self.serial.write((message + "\r").encode(self.encoding))

    def _write_echo(self, value: bool):
        self._write(f"SE{int(value)}")
        self._read("!\r")

    def write_set_point(self, temperature: Quantity):
        if not (self.temp_limits[0] <= temperature <= self.temp_limits[1]):
            raise ValueError(f"Temperature outside temperature limits."
                             f"\nGiven: {temperature}\nLimits: {self.temp_limits} ")

        temperature = float(temperature.to(Unit.C).v)
        temperature_string = f"{int(temperature):03}" + f"{temperature - int(temperature):0.2f}"[1:]
        self._write(f"SS{temperature_string}")
        self._read("!\r")

    def write_on(self):
        self._write(f"SO1")
        self._read("!\r")

    def write_off(self):
        self._write(f"SO0")
        self._read("!\r")

    def write_high_alarm(self, temperature: Quantity):
        temperature = int(temperature.to(Unit.C).v)
        self._write(f"SH{temperature:03}")
        self._read("!\r")

    def write_low_alarm(self, temperature: Quantity):
        temperature = int(temperature.to(Unit.C).v)
        self._write(f"SL{temperature:03}")
        self._read("!\r")

    def write_pump_speed(self, speed: int):
        """
        Parameters
        ----------
        speed:
            must be between 5-100; and incriments of 5
        """
        if not (5 <= speed <= 100):
            raise ValueError("Pump speed must be between 5-100.")
        speed = int(speed / 5) * 5

        self._write(f"SM{speed:03}")
        self._read("!\r")

    def write_control(self, value: bool):
        """
        Parameters
        ----------
        value:
            True: External temperature control
            False: Internal temperature control
        """
        self._write(f"SJ{int(value)}")
        self._read("!\r")

    def read_set_point(self) -> Quantity:
        self._write(f"RS")
        reply = self.serial.read_until("\r")

        try:
            return float(reply[:-1]) * Unit.degC
        except Exception as e:
            logger.error(f"reply:{reply}")
            if self.serial.in_waiting:
                logger.error(f"reply2:{self.serial.read(self.serial.in_waiting)}")
            raise e

    def read_units(self) -> str:
        """

        Returns
        -------
        C or F
        """
        self._write(f"RU")
        reply = self.serial.read_until("\r").decode(self.encoding)
        try:
            return reply[:-1]
        except Exception as e:
            logger.error(f"reply:{reply}")
            if self.serial.in_waiting:
                logger.error(f"reply2:{self.serial.read(self.serial.in_waiting)}")
            raise e

    def read_internal_temp(self) -> Quantity:
        self._write(f"RT")
        reply = self.serial.read_until("\r")

        try:
            return float(reply[:-1]) * Unit.degC
        except Exception as e:
            logger.error(f"reply:{reply}")
            if self.serial.in_waiting:
                logger.error(f"reply2:{self.serial.read(self.serial.in_waiting)}")
            raise e

    def read_external_temp(self) -> Quantity:
        self._write(f"RR")
        reply = self.serial.read_until("\r")

        try:
            return float(reply[:-1]) * Unit.degC
        except Exception as e:
            logger.error(f"reply:{reply}")
            if self.serial.in_waiting:
                logger.error(f"reply2:{self.serial.read(self.serial.in_waiting)}")
            raise e

    def read_status(self) -> bool:
        """

        Returns
        -------
        True: running
        False: standby
        """
        self._write(f"RO")
        reply = self.serial.read_until("\r")

        try:
            return bool(reply[:-1])
        except Exception as e:
            logger.error(f"reply:{reply}")
            if self.serial.in_waiting:
                logger.error(f"reply2:{self.serial.read(self.serial.in_waiting)}")
            raise e

    def read_high_alarm(self) -> Quantity:
        """

        Returns
        -------
        True: running
        False: standby
        """
        self._write(f"RH")
        reply = self.serial.read_until("\r")

        try:
            return float(reply[:-1]) * Unit.degC
        except Exception as e:
            logger.error(f"reply:{reply}")
            if self.serial.in_waiting:
                logger.error(f"reply2:{self.serial.read(self.serial.in_waiting)}")
            raise e

    def read_low_alarm(self) -> Quantity:
        """

        Returns
        -------
        True: running
        False: standby
        """
        self._write(f"RL")
        reply = self.serial.read_until("\r")

        try:
            return float(reply[:-1]) * Unit.degC
        except Exception as e:
            logger.error(f"reply:{reply}")
            if self.serial.in_waiting:
                logger.error(f"reply2:{self.serial.read(self.serial.in_waiting)}")
            raise e

    def read_pump_speed(self) -> int:
        """

        Returns
        -------
        int from 5-100
        """
        self._write(f"RM")
        reply = self.serial.read_until("\r")

        try:
            return int(reply[:-1])
        except Exception as e:
            logger.error(f"reply:{reply}")
            if self.serial.in_waiting:
                logger.error(f"reply2:{self.serial.read(self.serial.in_waiting)}")
            raise e

    def read_alarm(self) -> bool:
        """

        Returns
        -------
        True: Fault
        False: No Fault
        """
        self._write(f"RF")
        reply = self.serial.read_until("\r")

        try:
            return bool(reply[:-1])
        except Exception as e:
            logger.error(f"reply:{reply}")
            if self.serial.in_waiting:
                logger.error(f"reply2:{self.serial.read(self.serial.in_waiting)}")
            raise e

    def read_version(self) -> str:
        """
        """
        self._write(f"RF")
        reply = self.serial.read_until("\r")

        try:
            return reply[:-1]
        except Exception as e:
            logger.error(f"reply:{reply}")
            if self.serial.in_waiting:
                logger.error(f"reply2:{self.serial.read(self.serial.in_waiting)}")
            raise e


class PolyRecirculatingBath(TempControl):

    def __init__(self,
                 name: str,
                 comport: str,
                 temp_limits: tuple[Quantity, Quantity] = (5 * Unit.degC, 60 * Unit.degC),
                 ):
        self.bath = PolyScienceBath(comport, temp_limits)
        super().__init__(name=name)

    def write_set_point(self, temperature: Quantity):
        """ write set point temperature """
        self.bath.write_set_point(temperature)

    def read_set_point(self) -> Quantity:
        """ read set point """
        return self.bath.read_set_point()

    def read_temperature(self) -> Quantity:
        """ Turn off light """
        return self.bath.read_internal_temp()

    def _activate(self):
        pass  # done on init

    def _deactivate(self):
        self.bath.deactivate()

    def _stop(self):
        self.bath.write_off()
