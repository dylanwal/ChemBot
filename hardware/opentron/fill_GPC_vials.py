from opentrons import protocol_api

metadata = {
    'apiLevel': '2.12',
    'protocolName': 'fill_gpc_vial',
    'description': 'well plate 384',
    'author': 'Me'
}


def run(protocol: protocol_api.ProtocolContext):
    protocol.set_rail_lights(False)
    tips_1000 = protocol.load_labware('opentrons_96_tiprack_1000ul', 3)
    pipette_1000 = protocol.load_instrument('p1000_single_gen2', mount='left', tip_racks=[tips_1000])
    pipette_1000.flow_rate.aspirate = 200
    pipette_1000.flow_rate.dispense = 200

    reservoir = protocol.load_labware("agilent_1_reservoir_290ml", 7)
    gpc_vials = protocol.load_labware("custom_40_tuberack_1500ul", 4)
    gpc_vials2 = protocol.load_labware("custom_40_tuberack_1500ul", 5)

    # pipette_1000.transfer(1400, reservoir['A1'],
    #                       gpc_vials.wells()[:30],
    #                       blow_out=True, blowout_location="destination well")
    pipette_1000.transfer(1400, reservoir['A1'],
                          gpc_vials2.wells()[:10],
                          blow_out=True, blowout_location="destination well")

    protocol.set_rail_lights(False)
