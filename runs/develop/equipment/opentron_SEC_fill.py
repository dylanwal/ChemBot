
from opentrons import protocol_api


# metadata
metadata = {
    "protocolName": "SEC_fill_with_solvent",
    "author": "Name <opentrons@example.com>",
    "description": "Simple protocol to get started using the OT-2",
}

# requirements
requirements = {"robotType": "OT-2", "apiLevel": "2.14"}


# protocol run function
def run(protocol: protocol_api.ProtocolContext):
    protocol.set_rail_lights(False)
    # labware
    SEC_plate1 = protocol.load_labware("custom_40_tuberack_1500ul", location="4")
    SEC_plate2 = protocol.load_labware("custom_40_tuberack_1500ul", location="5")
    SEC_plate3 = protocol.load_labware("custom_40_tuberack_1500ul", location="6")
    THF_reservor = protocol.load_labware("agilent_1_reservoir_290ml", location="7")

    tiprack = protocol.load_labware("opentrons_96_tiprack_1000ul", location="2")

    # pipettes
    pipette_1000uL = protocol.load_instrument("p1000_single", mount="left", tip_racks=[tiprack])
    pipette_1000uL.flow_rate.aspirate = 300
    pipette_1000uL.flow_rate.dispense = 300

    pipette_1000uL.pick_up_tip()

    wells = SEC_plate1.wells() + SEC_plate2.wells() + SEC_plate3.wells()
    wells = wells[:96]
    for well in wells:
        pipette_1000uL.aspirate(800, THF_reservor["A1"])
        pipette_1000uL.dispense(800, well)
    for i in range(int(len(wells)/2)):
        pipette_1000uL.aspirate(800, THF_reservor["A1"])
        pipette_1000uL.dispense(400, wells[2*i])
        pipette_1000uL.dispense(400, wells[2*i+1])

    if int(len(wells)/2) != len(wells)/2:
        pipette_1000uL.aspirate(400, THF_reservor["A1"])
        pipette_1000uL.dispense(400, wells[-1])

    protocol.set_rail_lights(False)
