
from opentrons import protocol_api


# metadata
metadata = {
    "protocolName": "to_SEC_vial",
    "author": "Name <opentrons@example.com>",
    "description": "Simple protocol to get started using the OT-2",
}

# requirements
requirements = {"robotType": "OT-2", "apiLevel": "2.14"}


# protocol run function
def run(protocol: protocol_api.ProtocolContext):
    protocol.set_rail_lights(False)
    # labware
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", location="1")
    SEC_plate1 = protocol.load_labware("custom_40_tuberack_1500ul", location="4")
    SEC_plate2 = protocol.load_labware("custom_40_tuberack_1500ul", location="5")
    SEC_plate3 = protocol.load_labware("custom_40_tuberack_1500ul", location="6")

    tiprack = protocol.load_labware("opentrons_96_tiprack_300ul", location="2")
    tiprack2 = protocol.load_labware("opentrons_96_tiprack_300ul", location="3")

    # pipettes
    pipette_300uL = protocol.load_instrument("p300_single", mount="right", tip_racks=[tiprack, tiprack2])
    pipette_300uL.flow_rate.aspirate = 10
    pipette_300uL.flow_rate.dispense = 50
    pipette_300uL.well_bottom_clearance.aspirate = 3
    pipette_300uL.well_bottom_clearance.dispense = 4

    wells = SEC_plate1.wells() + SEC_plate2.wells() + SEC_plate3.wells()
    for i, well in enumerate(plate.wells()):
        pipette_300uL.pick_up_tip()
        pipette_300uL.flow_rate.aspirate = 10
        pipette_300uL.aspirate(30, well)
        pipette_300uL.dispense(30, wells[i])
        pipette_300uL.flow_rate.aspirate = 50
        pipette_300uL.mix(1, 200, wells[i])
        pipette_300uL.drop_tip()

    protocol.set_rail_lights(False)
