import enum
import socket
import logging
import sys
import time
from datetime import datetime
import xml.etree.cElementTree as xml

logger = logging.getLogger("nmr")
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)


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
            while True:
                reply = self.socket.recv(8192)
                if reply:
                    root = xml.fromstring(reply.decode("utf-8"))
                    status = root.find("StatusNotification")
                    complete_element = status.find("Completed")
                    if complete_element is not None:
                        if complete_element.attrib["successful"]:
                            logger.info(
                                f"proton completed at: {datetime.now()} ({(datetime.now() - start).total_seconds()} sec)")
                        else:
                            logger.exception("Error during proton.")
                        # _ = self.socket.recv(8192)  # capture extra message sent
                        break

        except socket.error as e:
            logger.exception(f"Timeout during proton.")

        except Exception as e:
            logger.error("Issue on reply")
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


def continous(sample_name: str):
    counter = 0
    times = []
    with NMRComm("192.168.0.100", 13000) as nmr:
        nmr.set_sample(sample_name)
        while True:
            nmr.take_protron(
                scans=NMRScans.THIRTYTWO,
                aqtime=NMRAqTime.POINTEIGHT,
                reptime=NMRRepTime.ONE,
                pulse_angle=NMRPulseAngle.SIXTY
            )
            logger.info(f"{counter},{time.time()},{datetime.now()}")
            times.append(f"{counter},{time.time()},{datetime.now()}")
            counter += 1


def main():
    with NMRComm("192.168.0.100", 13000) as nmr:
        # nmr.set_solvent(NMRSolvents.DMSO)
        # nmr.set_sample("remote_test")
        # nmr.check_shim()
        nmr.take_protron(NMRScans.FOUR)


if __name__ == "__main__":
    # main()
    continous("DW2_6_flow")

