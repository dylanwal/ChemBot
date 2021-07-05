"""
Entry Point for robot
"""
import logging


import harvard_pumps


logging.basicConfig(filename=r'C:\Users\nicep\Desktop\log.txt', encoding='utf-8', level=logging.DEBUG)

serial = harvard_pumps.SerialLine(port="COM3")
a = harvard_pumps.HarvardPumps(serial_line=serial, name="syr_pump_rxn1", address=0, diameter=1, max_volume=10)
