import chembot

syringe = chembot.pumps.Syringe.get_syringe("hamilton_1010")
pump_1 = chembot.pumps.PumpHarvard(
    serial_line="serial_pump",
    address="0",
    name="pump_1",
    syringe=syringe
)

pump_2 = chembot.pumps.PumpHarvard(
    serial_line="serial_pump",
    address="1",
    name="pump_2",
    syringe=syringe
)

pump_3 = chembot.pumps.PumpHarvard(
    serial_line="serial_pump",
    address="2",
    name="pump_3",
    syringe=syringe
)

pumps = [pump_1, pump_2, pump_3]

chembot.utils.activate_multiple_equipment(pumps)
