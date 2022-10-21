from opentrons import protocol_api

metadata = {
    'apiLevel': '2.12',
    'protocolName': 'RAFT',
    'description': 'well plate 384',
    'author': 'Me'
    }

# wells = [
#     "A1",
#     "A2",
#     "A9",
#     "A16",
#     "A23",
#     "A24",
#     "B1",
#     "B2",
#     "B23",
#     "B24",
#     "C11",
#     "C14",
#     "D4",
#     "D21",
#     "E12",
#     "E13",
#     "F6",
#     "F19",
#     "G10",
#     "G15",
#     "H1",
#     "H8",
#     "H9",
#     "H10",
#     "H11",
#     "H12",
#     "H13",
#     "H14",
#     "H15",
#     "H16",
#     "H17",
#     "H24",
#     "I1",
#     "I8",
#     "I9",
#     "I10",
#     "I11",
#     "I12",
#     "I13",
#     "I14",
#     "I15",
#     "I16",
#     "I17",
#     "I24",
#     "J10",
#     "J15",
#     "K6",
#     "K19",
#     "L12",
#     "L13",
#     "M4",
#     "M21",
#     "N11",
#     "N14",
#     "O1",
#     "O2",
#     "O23",
#     "O24",
#     "P1",
#     "P2",
#     "P9",
#     "P16",
#     "P23",
#     "P24",
# ]
# ascii number 65-90

wells = [f"{chr(64+num)}12" for num in range(1, 17)] + [f"H{num}" for num in range(1, 25)] \
        + ["A1", "A2", "B1", "B2", "A24", "P1", "P24"]


def run(protocol: protocol_api.ProtocolContext):
    protocol.set_rail_lights(False)
    tips_300 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
    pipette_300 = protocol.load_instrument('p300_single_gen2', mount='right', tip_racks=[tips_300])

    pipette_300.flow_rate.aspirate = 30

    plate = protocol.load_labware('greiner_384_wellplate_110ul', 1)
    gpc_vials = protocol.load_labware("custom_40_tuberack_1500ul", 4)

    # for well in wells:
    pipette_300.transfer(75, gpc_vials['A1'],
                         [plate[well] for well in wells[:17]],
                         blow_out=True, blowout_location="destination well")
    pipette_300.transfer(75, gpc_vials['A2'],
                         [plate[well] for well in wells[17:34]],
                         blow_out=True, blowout_location="destination well")
    pipette_300.transfer(75, gpc_vials['A3'],
                         [plate[well] for well in wells[34:]],
                         blow_out=True, blowout_location="destination well")
    # pipette_300.transfer(75, gpc_vials['A4'],
    #                      [plate[well] for well in wells[51:]],
    #                      blow_out=True, blowout_location="destination well")
    protocol.set_rail_lights(False)

