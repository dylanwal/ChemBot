import enum
import socket
import logging
import time
from datetime import datetime
import xml.etree.cElementTree as xml
import pathlib
import traceback

from unitpy import Unit, Quantity
import numpy as np

from chembot.rabbitmq.messages import RabbitMessageAction
from chembot.configuration import config, create_folder
from chembot.equipment.sensors.sensor import Sensor
from chembot.utils.nmr_processing import nmr_check

logger = logging.getLogger(config.root_logger_name + ".nmr")


class MessageStates(str, enum.Enum):
    Ready = "Ready"
    Running = "Running"
    Stopping = "Stopping"


class MessageState:
    def __init__(self, timestamp: str, protocol: str, status: str, data_folder: str):
        self.timestamp = timestamp  # "09:33:15"
        self.protocol = protocol  # "1D EXTENDED+"
        self.status = status  # "Ready"
        self.data_folder = data_folder


class MessageProgress:
    def __init__(self, timestamp: str, protocol: str, percentage: int, seconds_remaining: int):
        self.timestamp = timestamp  # "09:33:15"
        self.protocol = protocol  # "1D EXTENDED+"
        self.percentage = percentage
        self.seconds_remaining = seconds_remaining


class MessageError:
    def __init__(self, timestamp: str, protocol: str, error: str):
        self.timestamp = timestamp  # "09:33:15"
        self.protocol = protocol  # "1D EXTENDED+"
        self.error = error


class MessageCompleted:
    def __init__(self, timestamp: str, protocol: str, completed: bool, successful: bool):
        self.timestamp = timestamp  # "09:33:15"
        self.protocol = protocol  # "1D EXTENDED+"
        self.completed = completed
        self.successful = successful


def parse_xml(xml_data: str):
    xml_data = xml_data.replace('<?xml version="1.0" encoding="utf-8"?>', '')
    root = xml.fromstring(xml_data)

    if root.find('.//StatusNotification') is not None:
        timestamp = root.find('.//StatusNotification').get('timestamp')

        if root.find('.//State') is not None:
            protocol = root.find('.//State').get('protocol')
            status = root.find('.//State').get('status')
            data_folder = root.find('.//State').get('dataFolder')
            return MessageState(timestamp, protocol, status, data_folder)
        if root.find('.//Progress') is not None:
            protocol = root.find('.//Progress').get('protocol')
            percentage = int(root.find('.//Progress').get('percentage'))
            seconds_remaining = int(root.find('.//Progress').get('secondsRemaining'))
            return MessageProgress(timestamp, protocol, percentage, seconds_remaining)
        if root.find('.//Error') is not None:
            protocol = root.find('.//Error').get('protocol')
            error = root.find('.//Error').get('error')
            return MessageError(timestamp, protocol, error)
        if root.find('.//Completed') is not None:
            protocol = root.find('.//Completed').get('protocol')
            completed = root.find('.//Completed').get('completed')
            completed = True if completed == "true" else False
            successful = root.find('.//Completed').get('successful')
            successful = True if successful == "true" else False
            return MessageCompleted(timestamp, protocol, completed, successful)

    raise ValueError(f"Not recognized. \n{xml_data}")


class NMRSolvents(enum.Enum):
    UNKNOWN = 0
    NONE = 1
    ACETONE = 2
    ACETONITRILE = 3
    BENZENE = 4
    CHLOROFORM = 5
    CYCLOHEXANE = 6
    DMSO = 7
    ETHANOL = 8
    METHANOL = 9
    PYRIDINE = 10
    TMS = 11
    THF = 12
    TOLUENE = 13
    TFA = 14
    WATER = 15
    OTHER = 16


class NMRScans(enum.Enum):
    ONE = 1
    FOUR = 4
    EIGHT = 8
    SIXTEEN = 16
    THIRTYTWO = 32
    SIXTYFOUR = 64
    ONETWENTYEIGHT = 128
    TWOHOUNDREDFIFTYSIX = 256


class NMRAqTime(enum.Enum):
    POINTFOUR = 0.4
    POINTEIGHT = 0.8
    ONEPOINTSIX = 1.6
    THREEPOINTTWO = 3.2
    SIXPOINTFOUR = 6.4


class NMRRepTime(enum.Enum):
    ONE = 1
    TWO = 2
    FOUR = 4
    SEVEN = 7
    TEN = 10
    FIFTEEN = 15
    THIRTY = 30
    SIXTY = 60
    ONETWENTHY = 120


class NMRPulseAngle(enum.Enum):
    THIRTY = 30
    FOURTYFIVE = 45
    SIXTY = 60
    NINTY = 90


class NMRComm:
    def __init__(self, ip_address: str, port: int = 13000):
        self.ip_address = ip_address
        self.port = port
        self._connected = False
        self.socket: socket.socket = None

        self.open_connection()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()

    @property
    def connected(self) -> bool:
        return self._connected

    def open_connection(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip_address, self.port))
        logger.info("Connection to NMR established.")
        self._connected = True

    def close_connection(self):
        self.socket.close()
        logger.info("Connection to NMR closed.")
        self._connected = False

    def _send(self, message: xml.Element):
        message = xml.tostring(message, encoding="UTF-8")
        self.socket.send(message)

    def _look_for_reply(self):
        # self.socket.settimeout(1.)
        chunk = ""
        old = ""
        try:
            while True:
                if chunk:
                    old = chunk
                chunk = self.socket.recv(8192)
                if chunk:
                    logger.info(chunk.decode())
        except socket.error as e:
            self.socket.settimeout(None)

        return chunk, old

    def stop(self):
        self.close_connection()
        self.open_connection()

    def set_sample(self, name: str):
        message = xml.Element("Message")
        set_ = xml.SubElement(message, "Set")
        xml.SubElement(set_, "Sample").text = name

        self._send(message)
        logger.info(f"sample name set to: {name}")

    def set_solvent(self, solvent: NMRSolvents):
        message = xml.Element("Message")
        set_ = xml.SubElement(message, "Set")
        xml.SubElement(set_, "Solvent").text = solvent.name

        self._send(message)
        logger.info(f"solvent set to: {solvent.name}")

    def set_folder(self, folder: str):
        message = xml.Element("Message")
        set_ = xml.SubElement(message, "Set")
        folder = xml.SubElement(set_, "DataFolder")
        xml.SubElement(set_, "UserFolder").text = folder

        self._send(message)
        logger.info(f"folder set to: {folder}")

    def take_protron(self,
                     scans: NMRScans = NMRScans.THIRTYTWO,
                     aqtime: NMRAqTime = NMRAqTime.POINTEIGHT,
                     reptime: NMRRepTime = NMRRepTime.ONE,
                     pulse_angle: NMRPulseAngle = NMRPulseAngle.SIXTY
                     ):
        message = xml.Element("Message")
        start = xml.SubElement(message, "Start", protocol='1D EXTENDED+')
        xml.SubElement(start, "Option", name="Number", value=str(scans.value))
        xml.SubElement(start, "Option", name="AcquisitionTime", value=str(aqtime.value))
        xml.SubElement(start, "Option", name="RepetitionTime", value=str(reptime.value))
        xml.SubElement(start, "Option", name="PulseAngle", value=str(pulse_angle.value))

        self.socket.settimeout(reptime.value + 5)
        self._send(message)
        start = datetime.now()
        logger.info(f"proton started: {start}")
        try:
            _error_counter = 100
            while True:
                reply = self.socket.recv(8192)
                if reply:
                    try:
                        raw_message = reply.decode("utf-8")
                        if raw_message.count('<?xml version="1.0" encoding="utf-8"?>') > 1:
                            # if multiple message, take first
                            messages = raw_message.split('<?xml version="1.0" encoding="utf-8"?>')
                            messages = [message for i, message in messages if i % 2 == 1]
                        else:
                            messages = [raw_message]
                        for text in messages:
                            message = parse_xml(text)
                            if isinstance(message, MessageCompleted):
                                if message.successful:
                                    logger.info(
                                        f"proton completed at: {datetime.now()} ({(datetime.now() - start).total_seconds()} sec)")
                                    return
                                raise ValueError("NMR not successful.")
                    except Exception as e:
                        logger.error("Issue on reply(inner)")
                        logger.error(traceback.format_exc())
                        if reply:
                            logger.error(reply.decode("utf-8"))
                        logger.error(e)
                        _error_counter -= 1
                        if _error_counter == 0:
                            raise e

        except socket.error as e:
            logger.exception(f"Timeout during proton.")

        except Exception as e:
            logger.error("Issue NMR")
            if reply:
                logger.error(reply.decode("utf-8"))
            logger.error(e)

    def check_shim(self):
        message = xml.Element("Message")
        xml.SubElement(message, "CheckShimRequest")

        self._send(message)
        chunk, old = self._look_for_reply()
        logger.info(f"chunk: {chunk}\nold: {old}")

    def quick_shim(self):
        message = xml.Element("Message")
        xml.SubElement(message, "QuickShimRequest")

        self._send(message)
        chunk, old = self._look_for_reply()
        logger.info(f"chunk: {chunk}\nold: {old}")

    def power_shim(self):
        message = xml.Element("Message")
        xml.SubElement(message, "PowerShimRequest")

        self._send(message)
        chunk, old = self._look_for_reply()
        logger.info(f"chunk: {chunk}\nold: {old}")


class NMR(Sensor):
    SCANS = NMRScans
    SOLVENTS = NMRSolvents
    AQTIME = NMRAqTime
    REPTIME = NMRRepTime
    PULSEANGLE = NMRPulseAngle
    _method_path = str(pathlib.Path(__file__).parent)

    @property
    def _data_path(self):
        path = config.data_directory / pathlib.Path("nmr")
        create_folder(path)
        return path

    def __init__(self, name: str, ip_address: str, port: int):
        super().__init__(name)
        self._runner = NMRComm(ip_address, port)

    def _activate(self):
        pass

    def _deactivate(self):
        self._runner.close_connection()

    def _stop(self):
        self._runner.stop()

    def _write_measure(self,
                       scans: NMRScans = NMRScans.THIRTYTWO,
                       aqtime: NMRAqTime = NMRAqTime.POINTEIGHT,
                       reptime: NMRRepTime = NMRRepTime.ONE,
                       pulse_angle: NMRPulseAngle = NMRPulseAngle.SIXTY
                       ) -> np.ndarray:
        self._runner.take_protron(scans, aqtime, reptime, pulse_angle)
        return 0  # TODO

    def write_name(self, name: str):
        self._runner.set_sample(name)

    def write_measure(self,
                      scans: NMRScans = NMRScans.EIGHT,
                      aqtime: NMRAqTime = NMRAqTime.THREEPOINTTWO,
                      reptime: NMRRepTime = NMRRepTime.TEN,
                      pulse_angle: NMRPulseAngle = NMRPulseAngle.SIXTY,
                      ) -> np.ndarray:
        # switch valve to reactor
        self.rabbit.send(
            RabbitMessageAction("valve_five", self.name, "write_move", kwargs={"position": "NMR"})
        )
        time.sleep(2)

        # wait for plug
        flow_rate = 0 * Unit("ml/min")
        pumps = ["pump_one", "pump_two", "pump_three", "pump_four"]
        for pump in pumps:
            flow_rate += self.rabbit.send_and_consume(
                RabbitMessageAction(pump, self.name, "read_flow_rate"), timeout=3, error_out=True
            ).value
        vol = 3.14 * (10 * Unit.cm) * (0.03 * Unit.inch / 2) ** 2
        if flow_rate.v == 0:
            flow_rate = 0.1 * Unit("ml/min")
        time_ = vol / flow_rate
        time.sleep(time_.to("s").v)

        # switch back
        self.rabbit.send(
            RabbitMessageAction("valve_five", self.name, "write_move", kwargs={"position": "waste"})
        )
        time.sleep(2)

        # # flow plug
        self.rabbit.send(
            RabbitMessageAction("pump_five", self.name, "write_infuse",
                                kwargs={"volume": 0.263 * Unit("ml"), "flow_rate": 0.263 * Unit("ml/min")}
                                )
        )
        time.sleep(60)

        # take NMR
        for i in range(5):
            # take quick NMR to see if signal
            self.write_name("temp_")
            self._runner.take_protron(
                scans=NMRScans.ONE,
                aqtime=NMRAqTime.POINTEIGHT,
                reptime=NMRRepTime.ONE,
                pulse_angle=NMRPulseAngle.SIXTY
            )
            if nmr_check(r"C:\Users\Robot2\Desktop\Dylan\NMR\Magritek\temp_"):
                # take good nmr
                self.write_name("DW2")
                time.sleep(reptime.value - 1)
                self._runner.take_protron(scans, aqtime, reptime, pulse_angle)
                break
            else:
                logger.info("No signal. Move and retry NMR")
                self.rabbit.send(
                    RabbitMessageAction("pump_five", self.name, "write_infuse",
                                        kwargs={"volume": 0.01 * Unit.ml, "flow_rate": 0.2 * Unit("ml/min")})
                )
                time.sleep(8)
        else:
            logger.warning("No NMR signal found after 5 tries")

        return 0  # TODO
