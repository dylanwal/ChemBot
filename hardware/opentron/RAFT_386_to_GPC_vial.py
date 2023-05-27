from opentrons import protocol_api

metadata = {
    'apiLevel': '2.12',
    'protocolName': 'add sample to gpc vial',
    'description': 'well plate 384',
    'author': 'Me'
}

wells = [f"{chr(64+num)}12" for num in range(1, 17)] + [f"H{num}" for num in range(1, 25)] \
        + ["A1", "A2", "B1", "B2", "A24", "P1", "P24"]


def run(protocol: protocol_api.ProtocolContext):
    protocol.set_rail_lights(False)
    tips_300 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
    pipette_300 = protocol.load_instrument('p300_single_gen2', mount='right', tip_racks=[tips_300])

    pipette_300.flow_rate.aspirate = 4
    pipette_300.flow_rate.dispense = 50

    plate = protocol.load_labware('greiner_384_wellplate_110ul', 1)
    gpc_vials = protocol.load_labware("custom_40_tuberack_1500ul", 4)
    gpc_vials2 = protocol.load_labware("custom_40_tuberack_1500ul", 5)

    # for well in wells:
    sample_vial_wells = gpc_vials.wells() + gpc_vials2.wells()
    for i, well in enumerate(wells):
        pipette_300.transfer(20, plate[well],
                          sample_vial_wells[i],
                          blow_out=True, blowout_location="destination well", mix_after=(2, 20))

    protocol.set_rail_lights(False)
