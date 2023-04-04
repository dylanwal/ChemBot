
import chembot

print(chembot.config.logging_dir)

# comm
serial1_pumps = chembot.comm.(

)


# pumps
syringe = chembot.pumps.Syringe.get_syringe("hamilton_1010")
pump = chembot.pumps.PumpHarvard(
    serial_line="COM3",
    address="0",
    name=__name__,
    syringe=syringe
)

pump.activate()


# values
valve = chembot.valves.ValveServo(
    config="3L",
    ports =
)


valve.activate()
