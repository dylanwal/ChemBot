# Example for micropython.org device, RP2040 PIO mode
# Connections:
# Pin # | HX711
# ------|-----------
# 12    | data_pin
# 13    | clock_pin
#

from hx711 import HX711
from machine import Pin

pin_OUT = Pin(1, Pin.IN, pull=Pin.PULL_DOWN)
pin_SCK = Pin(0, Pin.OUT)

hx711 = HX711(pin_SCK, pin_OUT)

hx711.tare()
zero = hx711.read_average(10)
while True:
    print(hx711.read_average(10) - zero)