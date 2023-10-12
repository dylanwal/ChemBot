# Socket client to send commands to server on NMR computer
import enum
import socket
import time
import os
import logging
from datetime import datetime

# For parsing Spinsolve output
import xml.etree.ElementTree as ET

logger = logging.getLogger("NMR_log")
logger.setLevel(logging.INFO)


class NMRSolvents(enum.Enum):
    UNKNOWN = 1
    NONE = 2
    ACETONE = 3
    ACETONITRILE = 4
    BENZENE = 5
    CHLOROFORM = 6
    CYCLOHEXANE = 7
    DMSO = 8
    ETHANOL = 9
    METHANOL = 10
    PYRIDINE = 11
    TMS = 12
    THF = 13
    TOLUENE = 14
    TFA = 15
    WATER = 16
    OTHER = 17


class SpinsolveController:
    options_scans = (1, 4, 16, 32, 64, 128, 256)
    options_aqtime = (0.4, 0.8, 1.6, 3.2, 6.4)
    options_reptime = (1, 2, 4, 7, 10, 15, 30, 60, 120)
    options_pulse_angle = (30, 45, 60, 90)

    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(15)
        self.connected = False
        self.is_ready = False

    def __enter__(self):
        self.open_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()

    def parseMessage(self, xml):
        root = ET.fromstring(xml)

    def open_connection(self):
        try:
            self.s.connect((self.ip, self.port))
            logger.info('Connected to NMR server successfully!')
            self.connected = True
            self.is_ready = True

        # Handle anticipated errors within socket.error
        except socket.error as e:
            # Handle error when socket server on NMR computer has not yet been created
            if e.errno == 10061:  # This is error code corresponding to this particular case
                print('Could not connect to NMR server because it has not been created yet')
                print('Do you need to run "start_nmr_server.bat" on NMR computer?')

            # Handle error when socket client is already connected to socket server
            elif e.errno == 10056:  # This is error code corresponding to this particular case
                print('Already connected to NMR server, no need to connect again!')
            raise e

    def close_connection(self):
        self.send_msg('Close', wait_response=False)
        self.s.shutdown(1)
        self.s.close()
        logger.info('Disconnected from Spinsolve, closed NMR socket client.')
        self.connected = False

    def send_msg(self, msg, wait_response=True):
        msg = msg.encode("utf-8")
        try:
            self.is_ready = False
            self.s.sendall(msg)
            response = ''
            if wait_response:
                response = self.s.recv(2048).decode("utf-8").strip()

                self.is_ready = True
                return response

        except Exception as e:
            print(e)
            self.is_ready = True
            return 1  # error

    def setSampleName(self, SampleName):
        self.s.settimeout(None)
        self.send_msg('Sample,{}'.format(SampleName), wait_response=False)
        time.sleep(.1)

    def setSolvent(self, solvent: NMRSolvents):
        if isinstance(solvent, NMRSolvents):
            logger.exception("Invalid Solvent.")
            return

        self.send_msg('Solvent,{}'.format(solvent.name.lower()), wait_response=False)
        time.sleep(.1)

    def setCustomName(self, CustomName):
        self.s.settimeout(None)
        self.send_msg('Custom,{}'.format(CustomName), wait_response=False)
        time.sleep(.1)

    def setFolder(self, FolderPath):
        # Look for a folder on the NMR laptop inside C:/PROJECTS/DATA/Magritek
        head = ''
        tail = FolderPath
        EffPath = 'c:/PROJECTS/DATA/Magritek'
        AccuPath = ''
        while tail and not tail == '//SPA3513/NMRdata/Magritek':
            [tail, head] = os.path.split(tail)
            AccuPath = os.path.join(head, AccuPath)
        if tail:
            EffPath = os.path.join(EffPath, AccuPath).replace("\\", "/").strip("/")
            self.send_msg('Folder,{}'.format(EffPath), wait_response=False)
        else:
            print('Folder error.')

    def getFolder(self):
        # Look for a folder on the NMR laptop inside C:/PROJECTS/DATA/Magritek
        response = self.send_msg('QueryFolder')
        head = ''
        tail = response
        EffPath = '//SPA3513/NMRdata/Magritek'
        AccuPath = ''
        while tail and not tail.casefold() == 'c:/PROJECTS/DATA/Magritek'.casefold():
            [tail, head] = os.path.split(tail)
            AccuPath = os.path.join(head, AccuPath)
        if tail:
            EffPath = os.path.join(EffPath, AccuPath).replace("\\", "/").strip("/")
            return EffPath
        else:
            print('Folder error.')
            return 'N/A'

    def queryProtocols(self):
        response = self.send_msg('QueryProtocols')
        print(response)
        root = ET.fromstring(response)
        for protocol in root.iter('Protocol'):
            print(protocol.text)

    def doProton(self, nscans: int = 16, aqtime=6.4, reptime=7, pulse=60):
        if nscans not in self.options_scans:
            raise ValueError('nscans value not valid, using default (16)')
        if aqtime not in self.options_aqtime:
            raise ValueError('aqtime value not valid, using default (6.4)')
        if (reptime not in self.options_reptime) or reptime < aqtime:
            raise ValueError('reptime value not valid, using first value available ({})'.format(reptime))
        if pulse not in self.options_pulse_angle:
            raise ValueError('pulse value not valid, using default (60)')

        self.s.settimeout(nscans * reptime * 1.3 + 15)  # has to include the request time plus 15s of server timeout
        response = self.send_msg('Proton+,{},{},{},{}'.format(int(nscans), float(aqtime), int(reptime), int(pulse)))
        self.s.settimeout(15)

        if response == 1:
            # An error occurred in the message exchange
            return 1

        root = ET.fromstring(response)
        if root[0][0].tag == 'Error':
            print('Error in Proton+.')
            return 1
        else:
            timestamp = root[0].get('timestamp')
            protocol = root[0][0].get('protocol')
            dataFolder = root[0][0].get('dataFolder')
            print('Proton successful, stored in {}'.format(dataFolder))
            return [timestamp, protocol, dataFolder]

    def doShim(self, ShimType):
        if ShimType == 'Check':
            self.s.settimeout(15 * 2 + 15)  # has to include the request effective time plus 15s of server timeout
        elif ShimType == 'Quick':
            self.s.settimeout(15 * 60 * 2 + 15)
        elif ShimType == 'Power':
            self.s.settimeout(45 * 60 * 2 + 15)
        response = self.send_msg('{}Shim'.format(ShimType))
        self.s.settimeout(15)

        root = ET.fromstring(response)
        if root[0][5].text == 'true':
            print('System is ready LW = ', root[0][3].text, ', BW = ', root[0][4].text)
        else:
            print('System is NOT ready LW = ', root[0][3].text, ', BW = ', root[0][4].text)

        return [root[0][0].text == 'true', root[0][1].text == 'true', root[0][2].text == 'true', root[0][3].text,
                root[0][4].text, root[0][5].text == 'true']

    # Function to send commands using command line interface
    def commandLine(self):
        user_input = input("\n Type command (CheckShim, QueryProtocols, Proton, Proton+, connect, close, or other): ")
        if user_input == "CheckShim":
            [Tright, Tstable, lockstable, LineWidth, BaseWidth, IsReady] = self.doShim("Check")
            self.commandLine()
        elif user_input == "QueryProtocols":
            self.queryProtocols()
            self.commandLine()
        elif user_input == "Solvent":
            SolventName = input("\n   Solvent: ")
            self.setSolvent(SolventName)
        elif user_input == "Proton":
            protonInfo = self.doProton()
            self.commandLine()
        elif user_input == "Proton+":
            nscans = input("\n   nscans [1,4,16,32,64,128,256]: ")
            aqtime = input("\n   aqtime [0.4,0.8,1.6,3.2,6.4]: ")
            reptime = input("\n   reptime [1,2,4,7,10,15,30,60,120]: ")
            pulse = input("\n   pulse [30,45,60,90]: ")
            protonInfo = self.doProton(int(nscans), float(aqtime), int(reptime), int(pulse))
            self.commandLine()
        elif user_input == "connect":
            self.serverConnect()
            self.commandLine()
        elif user_input == "close":
            self.serverDisconnect()
        else:
            user_input = str(user_input)
            self.send_msg(user_input)
            self.commandLine()

    def continuous_proton(self, nscans: int = 16, aqtime=6.4, reptime=7, pulse_anlge=60):
        counter = 0
        try:
            while True:
                self.doProton(nscans, aqtime, reptime, pulse_anlge)
                logger.info(f"scan {counter} complete at: {datetime.now()}")
                counter += 1
        except KeyboardInterrupt:
            logger.info("keyboard Interrupt.")


if __name__ == '__main__':
    with SpinsolveController(ip='169.254.157.62', port=7125) as c:
        c.setSolvent(NMRSolvents.WATER)
        c.continuous_proton(
            nscans=32,
            aqtime=c.options_aqtime[1],
            reptime=c.options_reptime[0],
            pulse_anlge=c.options_pulse_angle[2]
        )
