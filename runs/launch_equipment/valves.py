
import chembot

from runs.launch_equipment.names import NamesValves, NamesSerial

config_front = chembot.equipment.valves.ValveConfiguration.get_configuration("4L")
config_front.ports[0].name = "to_reactor"
config_front.ports[1].name = "to_pump"
config_front.ports[2].name = "to_fill"
config_front.ports[3].name = "blocked"
config_front.ports[3].blocked = True

config_front.positions[0].setting = 1900  # calibrated on 7/7/23 DW
config_front.positions[0].name = "flow"
config_front.positions[1].setting = 4200  # calibrated on 7/7/23 DW
config_front.positions[1].name = "fill"
config_front.positions[2].setting = 6225  # calibrated on 7/7/23 DW
config_front.positions[3].setting = 8450  # calibrated on 7/7/23 DW

valve_front = chembot.equipment.valves.ValveServo(
    name=NamesValves.FRONT,
    communication=NamesSerial.PICO2,
    configuration=config_front,
    pin=5,
)
# valve_front.activate()

config_middle = chembot.equipment.valves.ValveConfiguration.get_configuration("4L")
config_middle.ports[0].name = "to_reactor"
config_middle.ports[1].name = "to_pump"
config_middle.ports[2].name = "to_fill"
config_middle.ports[3].name = "to_air"
# config_middle.ports[3].blocked = True

config_middle.positions[0].setting = 1638  # calibrated on 7/7/23 DW
config_middle.positions[0].name = "flow"
config_middle.positions[1].setting = 3932  # calibrated on 7/7/23 DW
config_middle.positions[1].name = "fill"
config_middle.positions[2].setting = 6225  # calibrated on 7/7/23 DW
config_middle.positions[3].setting = 8191  # calibrated on 7/7/23 DW
config_middle.positions[3].name = "flow_air"

valve_middle = chembot.equipment.valves.ValveServo(
    name=NamesValves.MIDDLE,
    communication=NamesSerial.PICO2,
    configuration=config_middle,
    pin=6,
)
# valve_middle.activate()

config_back = chembot.equipment.valves.ValveConfiguration.get_configuration("3S")
config_back.ports[0].name = "to_pump"
config_back.ports[1].name = "to_air"
config_back.ports[2].name = "block"
config_back.ports[3].name = "to_reactor"
config_back.ports[2].blocked = True

config_back.positions[0].setting = 2250  # calibrated on 7/7/23 DW
config_back.positions[0].name = "fill"
config_back.positions[1].setting = 4400  # calibrated on 7/7/23 DW
config_back.positions[2].setting = 6450  # calibrated on 7/7/23 DW
config_back.positions[2].name = "flow"

valve_back = chembot.equipment.valves.ValveServo(
    name=NamesValves.BACK,
    communication=NamesSerial.PICO2,
    configuration=config_back,
    pin=7,
)
# valve_back.activate()

config_analytical = chembot.equipment.valves.ValveConfiguration.get_configuration("4L")
config_analytical.ports[0].name = "to_waste"
config_analytical.ports[1].name = "to_reactor"
config_analytical.ports[2].name = "to_IR"
config_analytical.ports[3].name = "blocked"
config_analytical.ports[3].blocked = True

config_analytical.positions[0].setting = 1900  # calibrated on 7/7/23 DW
config_analytical.positions[0].name = "flow"
config_analytical.positions[1].setting = 4200  # calibrated on 7/7/23 DW
config_analytical.positions[1].name = "fill"
config_analytical.positions[2].setting = 6225  # calibrated on 7/7/23 DW
config_analytical.positions[3].setting = 8450  # calibrated on 7/7/23 DW

valve_analytical = chembot.equipment.valves.ValveServo(
    name=NamesValves.ANALYTICAL,
    communication=NamesSerial.PICO2,
    configuration=config_analytical,
    pin=8,
)
# valve_analytical.activate()


with chembot.utils.EquipmentManager() as manager:
    manager.add([valve_front, valve_middle, valve_back, valve_analytical])
    manager.activate()
