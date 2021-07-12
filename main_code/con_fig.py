"""
Configuration File:

This contains dictionaries of the active components on the system.
(Un)comment or add/delete to add or remove a component from the robot.

Components:
* Reactor
* Valves
* Phase sensors
* Temperature probes
* Pumps
* Heaters/Coolers
* Lights


"""
import pint

u = pint.UnitRegistry()
uq = u.Quantity

"""
Reactor:


"""
# reactor = {
#     "len": 1,
#     "radius": 0.01,
#     "sensors": [
#         temp1,
#         temp2,
#         temp3
#     ],
#     "max_pres": 50,
#     "max_temp": 100
# }


"""
Valves:

format:
"subclass": {
        "name": any unique name for equipment
        "min_temp": minimum safe operating temperature (safety check)
        "max_temp": maximum safe operating temperature (safety check)
        "min_pres": minimum safe operating pressure (safety check)
        "max_pres": maximum safe operating pressure (safety check)
                
    <there may addition parameters depending on the class>
}


"""
valves = {
    "syringe_pump_valve_1": {
        "class": "ValveServo",
        "max_temp": uq(80, "degC"),
        "max_pres": 50 * u("psi"),
        "config": "4L",
        "ports": {
            1: {
                "name": "air_source",
                "link": "air_source"
            },
            2: {
                "name": "to_reactor",
                "link": "reactor"
            },
            3: {
                "name": "syringe_pump",
                "link": "air_pump"
            }
        },
        "start_pos": 2,
        "servo_timing": [
            545,
            1190,
            1820,
            2480,
        ],
        "port": "COM9"
    }
}

#     "pump_2": {
#         "port": "COM9",
#         "pin": 11,
#         "positions": [
#             ["P1", 545],
#             ["P2", 1190],
#             ["P3", 1820],
#             ["P4", 2480]
#         ]
#     },
#     "pump_air": {
#         "port": "COM9",
#         "pin": 12,
#         "positions": [
#             ["P1", 545],
#             ["P2", 1190],
#             ["P3", 1820],
#             ["P4", 2480]
#         ]
#     }
#
# }

"""
Sensors:

"""
# sensors = {
#     "phase_sensor":1
# }
