# Socket client to send commands to server on NMR computer
# Federico Florit, 2/27/23, based on HPLC client code

import socket
import errno
import time
import os

# For parsing Spinsolve output
import xml.etree.ElementTree as ET


class SpinsolveController:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(15)
        self.connected = False
        self.is_ready = False
        self.serverConnect()

    def parseMessage(self, xml):
        root = ET.fromstring(xml)

    def serverConnect(self):
        try:
            self.s.connect((self.ip, self.port))
            print('Connected to NMR server successfully!')
            self.connected = True
            self.is_ready = True

        # Handle anticipated errors within socket.error
        except socket.error as e:
            # Handle error when socket server on NMR computer has not yet been created
            if e.errno == 10061:  # This is error code corresponding to this particular case
                print(e)
                print('Could not connect to NMR server because it has not been created yet')
                print('Do you need to run "start_nmr_server.bat" on NMR computer?')
            # Handle error when socket client is already connected to socket server
            elif e.errno == 10056:  # This is error code corresponding to this particular case
                print(e)
                print('Already connected to NMR server, no need to connect again!')
            # Handle any other error numbers within socket.error not handled above
            else:
                print(e)

        # Handle unanticipated errors
        except Exception as e:
            print(e)

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

        # # Handle anticipated errors within socket.error
        # except socket.error as e:
        # 	# Handle error when socket server on NMR computer has not yet been created
        # 	if e.errno == 10061: # This is error code corresponding to this particular case
        # 		print(e)
        # 		print('Cannot send command because you are not connected to NMR socket server')
        # 		print('Try re-connecting')
        # 	# Handle error when socket server on NMR computer was closed mid-connection
        # 	elif e.errno == 10054: # This is error code corresponding to this particular case
        # 		print(e)
        # 		print('NMR socket server on NMR computer was closed mid-connection')
        # 		print('Run "start_nmr_server.bat" on NMR computer and try re-connecting')
        # 	# Handle any other error numbers within socket.error not handled above
        # 	else:
        # 		print(e)
        # 	return 1 # error

        # Handle unanticipated errors
        except Exception as e:
            print(e)
            self.is_ready = True
            return 1  # error

    def setSampleName(self, SampleName):
        self.s.settimeout(None)
        self.send_msg('Sample,{}'.format(SampleName), wait_response=False)
        time.sleep(.1)

    def setSolvent(self, SolventName):
        if not SolventName in ['Unknown', 'None', 'Acetone', 'Acetonitrile', 'Benzene', 'Chloroform', 'Cyclohexane',
                               'DMSO', 'Ethanol', 'Methanol', 'Pyridine', 'TMS', 'THF', 'Toluene', 'TFA', 'Water',
                               'Other']:
            SolventName = 'Unknown'

        self.send_msg('Solvent,{}'.format(SolventName), wait_response=False)
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

    def doProton(self, nscans=16, aqtime=6.4, reptime=7, pulse=60):
        if not nscans in [1, 4, 16, 32, 64, 128, 256]:
            print('nscans value not valid, using default (16)')
            nscans = 16
        if not aqtime in [0.4, 0.8, 1.6, 3.2, 6.4]:
            print('aqtime value not valid, using default (6.4)')
            aqtime = 6.4
        if (not reptime in [1, 2, 4, 7, 10, 15, 30, 60, 120]) or reptime < aqtime:
            reptime = next((x for x in [1, 2, 4, 7, 10, 15, 30, 60, 120] if x > aqtime))
            print('reptime value not valid, using first value available ({})'.format(reptime))
        if not pulse in [30, 45, 60, 90]:
            print('pulse value not valid, using default (60)')
            pulse = 60

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

    def serverDisconnect(self):
        self.send_msg('Close', wait_response=False)
        self.s.shutdown(1)
        self.s.close()
        print('Disconnected from Spinsolve, closed NMR socket client.')
        self.connected = False

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


if __name__ == '__main__':
    nmr_computer_ip = '192.168.0.100' #'169.254.157.62'
    port = 7125

    c = SpinsolveController(nmr_computer_ip, port)
    c.commandLine()
