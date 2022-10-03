from opentrons import protocol_api

metadata = {
    'apiLevel': '2.12',
    'protocolName': 'RAFT',
    'description': 'well plate 96 with shading',
    'author': 'Me'
    }

# wells = [f"C{num}" for num in range(4, 10)] + [f"D{num}" for num in range(1, 13)] + [f"E{num}" for num in range(1, 13)]
wells = [f"B{num}" for num in [2,4,6,8,10]] + \
        [f"C{num}" for num in [3,5,7,9,11]] + \
        [f"D{num}" for num in [2,4,6,8,10]] + \
        [f"E{num}" for num in [3,5,7,9,11]] + \
        [f"F{num}" for num in [2,4,6,8,10]] + \
        ["G5", "G7"]


def run(protocol: protocol_api.ProtocolContext):
    protocol.set_rail_lights(False)
    tips_300 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
    pipette_300 = protocol.load_instrument('p300_single_gen2', mount='right', tip_racks=[tips_300])
    pipette_300.flow_rate.aspirate = 30

    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', 1)
    gpc_vials = protocol.load_labware("custom_40_tuberack_1500ul", 4)

    # for well in wells:
    pipette_300.transfer(150, gpc_vials['A1'],
                         [plate[well] for well in wells[:8]],
                         blow_out=True, blowout_location="destination well")
    pipette_300.transfer(150, gpc_vials['A2'],
                         [plate[well] for well in wells[8:16]],
                         blow_out=True, blowout_location="destination well")
    pipette_300.transfer(150, gpc_vials['A3'],
                         [plate[well] for well in wells[16:24]],
                         blow_out=True, blowout_location="destination well")
    pipette_300.transfer(150, gpc_vials['A4'],
                         [plate[well] for well in wells[24:]],
                         blow_out=True, blowout_location="destination well")
    protocol.set_rail_lights(False)














