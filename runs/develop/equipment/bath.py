"""PolyScience Circulating Bath"""
import logging
import time

from serial import Serial
from unitpy import Quantity, Unit


logger = logging.getLogger("bath")


class PolyScienceBath:
    def __init__(self,
                 comport: str,
                 temp_limits: tuple[Quantity, Quantity] = (5 * Unit.degC, 60 * Unit.degC),
                 encoding: str = "UTF8"
                 ):
        self.serial = Serial(comport, timeout=5)
        self.encoding = encoding

        self._activate()
        self._temp_limits = None
        self.temp_limits = temp_limits

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deactivate()

    def _activate(self):
        self.serial.flushInput()
        self.serial.flushOutput()
        self._write_echo(False)

    def deactivate(self):
        self.write_off()
        self.serial.close()

    def _read(self, expected_reply: str):
        reply = self.serial.read(len(expected_reply))
        logger.debug("read: " + reply.decode())
        try:
            if reply.decode() != expected_reply or self.serial.in_waiting:
                raise RuntimeError("unexpected reply")
        except Exception as e:
            logger.error(f"reply:{reply}")
            if self.serial.in_waiting:
                logger.error(f"reply2:{self.serial.read(self.serial.in_waiting)}")
            raise e

    def _write(self, message: str):
        logger.debug("write: " + message)
        self.serial.write((message + "\r").encode(self.encoding))

    def _write_echo(self, value: bool):
        self._write(f"SE{int(value)}")
        self._read("!\r")

    def write_set_point(self, temperature: Quantity):
        if not (self.temp_limits[0] <= temperature <= self.temp_limits[1]):
            raise ValueError(f"Temperature outside temperature limits."
                             f"\nGiven: {temperature}\nLimits: {self.temp_limits} ")

        temperature = float(temperature.to(Unit.degC).v)
        temperature_string = f"{int(temperature):03}" + f"{temperature - int(temperature):0.2f}"[1:]
        self._write(f"SS{temperature_string}")
        self._read("!\r")

    def write_on(self):
        self._write(f"SO1")
        self._read("!\r")

    def write_off(self):
        self._write(f"SO0")
        # self._read("!\r")

    def write_high_alarm(self, temperature: Quantity):
        temperature = int(temperature.to(Unit.degC).v)
        self._write(f"SH{temperature:03}")
        self._read("!\r")

    def write_low_alarm(self, temperature: Quantity):
        temperature = int(temperature.to(Unit.degC).v)
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


def main():
    import pathlib
    from utils.buffers.buffer_ping_pong import PingPongBuffer

    path = pathlib.Path(__file__).parent / "bath.csv"
    with PingPongBuffer(path) as buffer:
        with PolyScienceBath("COM17") as bath:
            while True:
                event = scheduler.get_event()
                if event():
                    event.run()
                else:
                    buffer.add_data((bath.read_set_point().v, bath.read_internal_temp().v))


def main_simple():
    with PolyScienceBath("COM16") as bath:
        bath.write_on()
        bath.write_set_point(25 * Unit.degC)
        print("waiting")
        time.sleep(60)

if __name__ == "__main__":
    main()
