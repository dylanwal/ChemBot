
import chembot

syringe = chembot.pumps.Syringe.get_syringe("hamilton_1010")
pump = chembot.pumps.PumpHarvard(
    serial_line="COM3",
    address="0",
    name=__name__,
    syringe=syringe
)

pump.activate()
