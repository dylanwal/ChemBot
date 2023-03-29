
import chembot

syringe = chembot.pumps.get_syringe("hamilton_1010")
pump = chembot.pumps.PumpHarvard(
    serial_line="COM3",
    address="0",
    name="pump_1",
    diameter=syringe.diameter,
    max_volume=syringe.volume,
)

pump.activate()
