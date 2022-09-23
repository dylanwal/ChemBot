from opentrons import protocol_api

metadata = {
    'apiLevel': '2.12',
    'protocolName': 'add sample to gpc vial',
    'description': 'well plate 384',
    'author': 'Me'
}

wells = [
    "A1",
    "A2",
    "A9",
    "A16",
    "A23",
    "A24",
    "B1",
    "B2",
    "B23",
    "B24",
    "C11",
    "C14",
    "D4",
    "D21",
    "E12",
    "E13",
    "F6",
    "F19",
    "G10",
    "G15",
    "H1",
    "H8",
    "H9",
    "H10",
    "H11",
    "H12",
    "H13",
    "H14",
    "H15",
    "H16",
    "H17",
    "H24",
    "I1",
    "I8",
    "I9",
    "I10",
    "I11",
    "I12",
    "I13",
    "I14",
    "I15",
    "I16",
    "I17",
    "I24",
    "J10",
    "J15",
    "K6",
    "K19",
    "L12",
    "L13",
    "M4",
    "M21",
    "N11",
    "N14",
    "O1",
    "O2",
    "O23",
    "O24",
    "P1",
    "P2",
    "P9",
    "P16",
    "P23",
    "P24",
]


def run(protocol: protocol_api.ProtocolContext):
    protocol.set_rail_lights(True)
    tips_300 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
    tips_1000 = protocol.load_labware('opentrons_96_tiprack_1000ul', 3)
    pipette_300 = protocol.load_instrument('p300_single_gen2', mount='right', tip_racks=[tips_300])
    pipette_1000 = protocol.load_instrument('p1000_single_gen2', mount='left', tip_racks=[tips_1000])

    pipette_300.flow_rate.aspirate = 20
    pipette_300.flow_rate.dispense = 20
    pipette_1000.flow_rate.aspirate = 400
    pipette_1000.flow_rate.dispense = 400

    plate = protocol.load_labware('greiner_384_wellplate_110ul', 1)
    reservoir = protocol.load_labware("agilent_1_reservoir_290ml", 7)
    gpc_vials = protocol.load_labware("custom_40_tuberack_1500ul", 5)
    # gpc_vials2 = protocol.load_labware("custom_40_tuberack_1500ul", 5)

    # pipette_1000.transfer(400, reservoir['A1'], [gpc_vials['A1'], gpc_vials['A8'], gpc_vials['E1'], gpc_vials['E8']])
    # pipette_300.transfer(20, plate['A1'], [gpc_vials['A1'], gpc_vials['A8'], gpc_vials['E1'], gpc_vials['E8']])

    pipette_1000.transfer(400, reservoir['A1'], gpc_vials.wells())
    pipette_300.transfer(20, plate['A1'], gpc_vials.wells())

    # fill_wells = gpc_vials.wells() # + gpc_vials2.wells()[:25]
    # pipette_1000.transfer(400, reservoir['A1'], fill_wells, blow_out=True, blowout_location="destination well")
    #
    # for i, well in enumerate(wells[len(gpc_vials.wells()):]):
    #     pipette_300.transfer(20, plate[well],
    #                       fill_wells[i],
    #                       blow_out=True, blowout_location="destination well", mix_after=(2, 20))

    protocol.set_rail_lights(False)
