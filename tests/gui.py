
example_registry = {
    "class": "EquipmentRegistry",
    "equipment": {
        "pico_serial": {
            "class": "EquipmentInterface",
            "name": "pico_serial",
            "class_": "PicoSerial",
            "state": {
                "enum": "EquipmentState",
                "value": 0
            },
            "actions": [
                {
                    "class": "Action",
                    "name": "write",
                    "description": "write stuff to pico",
                    "inputs": [
                        {
                            "class": "ActionParameter",
                            "name": "message",
                            "types": "str"
                        }
                    ]
                },
                {
                    "class": "Action",
                    "name": "read",
                    "description": "read stuff from pico",
                    "outputs": [
                        {
                            "class": "ActionParameter",
                            "name": "message",
                            "types": "str"
                        }
                    ]
                }
            ]
        },
        "red_led": {
            "class": "EquipmentInterface",
            "name": "red_led",
            "class_": "PicoLED",
            "state": {
                "enum": "EquipmentState",
                "value": 0
            },
            "actions": [
                {
                    "class": "Action",
                    "name": "write_on",
                    "description": "turn on light",
                },
                {
                    "class": "Action",
                    "name": "write_off",
                    "description": "turn off light",
                },
                {
                    "class": "Action",
                    "name": "write_power",
                    "description": "set light power",
                    "inputs": [
                        {
                            "class": "ActionParameter",
                            "name": "power",
                            "types": "float",
                            "range_": "[0:100]",
                            "unit": "kg"
                        }
                    ]
                }
            ]
        }
    }
}
