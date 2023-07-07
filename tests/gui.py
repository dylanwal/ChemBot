
example_registry = {
    "class": "EquipmentRegistry",
    "equipment": {
        "pico_serial": {
            "class": "EquipmentInterface",
            "class_name": "pico_serial",
            "class_": "PicoSerial",
            "state": {
                "enum": "EquipmentState",
                "value": 0
            },
            "actions": [
                {
                    "class": "Action",
                    "class_name": "write",
                    "description": "write stuff to pico",
                    "inputs": [
                        {
                            "class": "ActionParameter",
                            "class_name": "message",
                            "types": "str"
                        }
                    ]
                },
                {
                    "class": "Action",
                    "class_name": "read",
                    "description": "read stuff from pico",
                    "outputs": [
                        {
                            "class": "ActionParameter",
                            "class_name": "message",
                            "types": "str"
                        }
                    ]
                }
            ]
        },
        "red_led": {
            "class": "EquipmentInterface",
            "class_name": "red_led",
            "class_": "PicoLED",
            "state": {
                "enum": "EquipmentState",
                "value": 0
            },
            "actions": [
                {
                    "class": "Action",
                    "class_name": "write_on",
                    "description": "turn on light",
                },
                {
                    "class": "Action",
                    "class_name": "write_off",
                    "description": "turn off light",
                },
                {
                    "class": "Action",
                    "class_name": "write_power",
                    "description": "set light power",
                    "inputs": [
                        {
                            "class": "ActionParameter",
                            "class_name": "power",
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
