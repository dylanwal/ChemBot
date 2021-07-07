"""
Configuration File:

This contains dictionaries of the active components on the system.
(Un)comment or add/delete to add or remove a component from the robot.

Components:
* Valves
* Phase sensors
* Temperature probes
* Pumps
* Heaters/Coolers
* Lights


"""


"""
Valves:

format:
"class": {
    "name": str,
    "port": "COM#",
    "pin": int,
    "positions": list[[str, int]]  
                str = position name
                int = milliseconds or microseconds
                
    <there may addition parameters depending on the class>
}


"""
valves = {
    "pump_1": {
        "port": "COM9",
        "pin": 10,
        "positions": [
            ["P1", 545],
            ["P2", 1190],
            ["P3", 1820],
            ["P4", 2480]
        ]
    },
    "pump_2": {
        "port": "COM9",
        "pin": 11,
        "positions": [
            ["P1", 545],
            ["P2", 1190],
            ["P3", 1820],
            ["P4", 2480]
        ]
    },
    "pump_air": {
        "port": "COM9",
        "pin": 12,
        "positions": [
            ["P1", 545],
            ["P2", 1190],
            ["P3", 1820],
            ["P4", 2480]
        ]
    }

}