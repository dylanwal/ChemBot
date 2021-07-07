"""
Entry Point for robot
"""
import logging


import harvard_pumps


logging.basicConfig(filename=r'C:\Users\nicep\Desktop\log.txt', encoding='utf-8', level=logging.DEBUG)

serial = harvard_pumps.SerialLine(port="COM3")
a = harvard_pumps.HarvardPumps(serial_line=serial, name="syr_pump_rxn1", address=0, diameter=1, max_volume=10)

# import sys
# import logging
#
# logger = logging.getLogger(__name__)
# handler = logging.StreamHandler(stream=sys.stdout)
# logger.addHandler(handler)
#
#
# def handle_exception(exc_type, exc_value, exc_traceback):
#     if issubclass(exc_type, KeyboardInterrupt):
#         sys.__excepthook__(exc_type, exc_value, exc_traceback)
#         return
#
#     logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
#
#
# sys.excepthook = handle_exception
#

#
logging.basicConfig(filename=r'.\testing.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')
logging.info("\n\n")
logging.info("---------------------------------------------------")
logging.info("---------------------------------------------------")

