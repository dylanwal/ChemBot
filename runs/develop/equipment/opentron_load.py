import dataclasses

from opentrons import protocol_api

csv = [
    ['A1', 'BTPA', '', 'MA', ''],
    ['A2', 'BTPA', '', 'MMA', ''],
    ['A3', 'BTPA', '', 'St', ''],
    ['A4', 'BTPA', '', 'DMA', ''],
    ['A5', 'BTPA', '', 'isoprene', ''],
    ['A6', 'BTPA', '', 'tBuA', ''],
    ['A7', 'BTPA', '', 'Py', ''],
    ['A8', 'BTPA', '', 'MA', 'MMA'],
    ['A9', 'BTPA', '', 'MA', 'St'],
    ['A10', 'BTPA', '', 'MA', 'DMA'],
    ['A11', 'BTPA', '', 'MA', 'isoprene'],
    ['A12', 'BTPA', '', 'MA', 'tBuA'],
    ['B1', 'BTPA', '', 'MA', 'Py'],
    ['B2', 'CPADB', '', 'MA', ''],
    ['B3', 'CPADB', '', 'MMA', ''],
    ['B4', 'CPADB', '', 'St', ''],
    ['B5', 'CPADB', '', 'DMA', ''],
    ['B6', 'CPADB', '', 'isoprene', ''],
    ['B7', 'CPADB', '', 'tBuA', ''],
    ['B8', 'CPADB', '', 'Py', ''],
    ['B9', 'BTPA', 'CPADB', 'MA', ''],
    ['B10', 'BTPA', 'CPADB', 'MMA', ''],
    ['B11', 'BTPA', 'CPADB', 'St', ''],
    ['B12', 'BTPA', 'CPADB', 'DMA', ''],
    ['C1', 'BTPA', 'CPADB', 'isoprene', ''],
    ['C2', 'BTPA', 'CPADB', 'tBuA', ''],
    ['C3', 'BTPA', 'CPADB', 'Py', ''],
    ['C4', 'BTPA', 'CPADB', 'MA', 'MMA'],
    ['C5', 'BTPA', 'CPADB', 'MA', 'St'],
    ['C6', 'BTPA', 'CPADB', 'MA', 'DMA'],
    ['C7', 'BTPA', 'CPADB', 'MA', 'isoprene'],
    ['C8', 'BTPA', 'CPADB', 'MA', 'tBuA'],
    ['C9', 'BTPA', 'CPADB', 'MA', 'Py'],
    ['C10', 'CPADB', '', 'MA', 'MMA'],
    ['C11', 'CPADB', '', 'MA', 'St'],
    ['C12', 'CPADB', '', 'MA', 'DMA'],
    ['D1', 'CPADB', '', 'MA', 'isoprene'],
    ['D2', 'CPADB', '', 'MA', 'tBuA'],
    ['D3', 'CPADB', '', 'MA', 'Py'],
    ['D4', 'S', '', 'MA', ''],
    ['D5', 'S', '', 'MMA', ''],
    ['D6', 'S', '', 'St', ''],
    ['D7', 'S', '', 'DMA', ''],
    ['D8', 'S', '', 'isoprene', ''],
    ['D9', 'S', '', 'tBuA', ''],
    ['D10', 'S', '', 'Py', ''],
    ['D11', 'BTPA', 'S', 'MA', ''],
    ['D12', 'BTPA', 'S', 'MMA', ''],
    ['E1', 'BTPA', 'S', 'St', ''],
    ['E2', 'BTPA', 'S', 'DMA', ''],
    ['E3', 'BTPA', 'S', 'isoprene', ''],
    ['E4', 'BTPA', 'S', 'tBuA', ''],
    ['E5', 'BTPA', 'S', 'Py', ''],
    ['E6', 'S', '', 'MA', 'MMA'],
    ['E7', 'S', '', 'MA', 'St'],
    ['E8', 'S', '', 'MA', 'DMA'],
    ['E9', 'S', '', 'MA', 'isoprene'],
    ['E10', 'S', '', 'MA', 'tBuA'],
    ['E11', 'S', '', 'MA', 'Py'],
    ['E12', 'D', '', 'MA', ''],
    ['F1', 'D', '', 'MMA', ''],
    ['F2', 'D', '', 'St', ''],
    ['F3', 'D', '', 'DMA', ''],
    ['F4', 'D', '', 'isoprene', ''],
    ['F5', 'D', '', 'tBuA', ''],
    ['F6', 'D', '', 'Py', ''],
    ['F7', 'BTPA', 'D', 'MA', ''],
    ['F8', 'BTPA', 'D', 'MMA', ''],
    ['F9', 'BTPA', 'D', 'St', ''],
    ['F10', 'BTPA', 'D', 'DMA', ''],
    ['F11', 'BTPA', 'D', 'isoprene', ''],
    ['F12', 'BTPA', 'D', 'tBuA', ''],
    ['G1', 'BTPA', 'D', 'Py', ''],
    ['G2', 'D', '', 'MA', 'MMA'],
    ['G3', 'D', '', 'MA', 'St'],
    ['G4', 'D', '', 'MA', 'DMA'],
    ['G5', 'D', '', 'MA', 'isoprene'],
    ['G6', 'D', '', 'MA', 'tBuA'],
    ['G7', 'D', '', 'MA', 'Py'],
    ['G8', 'BTPA', '', 'DMA', ''],
    ['G9', 'BTPA', 'CPADB', 'DMA', ''],
    ['G10', 'BTPA', 'S', 'DMA', ''],
    ['G11', 'BTPA', 'D', 'DMA', ''],
    ['G12', 'BTPA', 'CPADB', 'St', ''],
    ['H1', 'BTPA', 'S', 'St', ''],
    ['H2', 'BTPA', 'D', 'St', ''],
    ['H3', 'BTPA', 'CPADB', 'MMA', ''],
    ['H4', 'BTPA', 'S', 'MMA', ''],
    ['H5', 'BTPA', 'D', 'MMA', ''],
    ['H6', 'BTPA', '', 'MA', ''],
    ['H7', 'CPADB', '', 'MA', ''],
    ['H8', 'S', '', 'MA', ''],
    ['H9', 'D', '', 'MA', ''],
    ['H10', 'BTPA', 'CPADB', 'MA', ''],
    ['H11', 'BTPA', 'S', 'MA', ''],
    ['H12', 'BTPA', 'D', 'MA', ''],
]


@dataclasses.dataclass
class Row:
    """
    [well, cta1, cta2, mon1, mon2, cat_vol(uL), cta1_vol(uL), cta2_vol(uL), mon1_vol(uL), mon2_vol(uL), dmso_vol(uL)]
    ['A1', 'BTPA', '', 'MA', '', 55.13729818, 63.52363805, 0.0, 81.31025671, 0.0, 0.0]

    """
    well: str
    cta1: str
    cta2: str  # | None
    mon1: str
    mon2: str  # | None


def load_data():
    data = []
    for row in csv:
        for i in range(len(row)):
            if row[i] == "":
                row[i] = None
        data.append(Row(*row))

    return data


def get_full_half_mon(data, key):
    full = [row.well for row in data if row.mon1 == key and row.mon2 is None]
    half = [row.well for row in data if row.mon1 == key and row.mon2 is not None] + [row.well for row in data if
                                                                                     row.mon2 == key]

    return full, half


def do_monomer(pipette, source, plate, data, key):
    full, half = get_full_half_mon(data, key)
    wells = [plate[name] for name in full]
    wells_half = [plate[name] for name in half]

    monomer_full = 81.31
    pipette.distribute(
        volume=monomer_full,
        source=source,
        dest=wells
    )
    pipette.distribute(
        volume=monomer_full / 2,
        source=source,
        dest=wells_half
    )


def get_full_half_cta(data, key):
    full = [row.well for row in data if row.cta1 == key and row.cta2 is None]
    half = [row.well for row in data if row.cta1 == key and row.cta2 is not None] + [row.well for row in data if
                                                                                     row.cta2 == key]

    return full, half


def do_cta(pipette, source, plate, data, key):
    full, half = get_full_half_cta(data, key)
    wells = [plate[name] for name in full]
    wells_half = [plate[name] for name in half]

    vol_full = 63.52
    pipette.distribute(
        volume=vol_full,
        source=source,
        dest=wells
    )
    pipette.distribute(
        volume=vol_full / 2,
        source=source,
        dest=wells_half
    )


# metadata
metadata = {
    "protocolName": "RAFT_DW2-11",
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
    mon_plate = protocol.load_labware("dw_8_tuberack_20000ul", location="4")
    cta_plate = protocol.load_labware("dw_8_tuberack_20000ul", location="5")
    # mon_plate = protocol.load_labware("corning_6_wellplate_16.8ml_flat", location="4")
    # cta_plate = protocol.load_labware("corning_6_wellplate_16.8ml_flat", location="5")

    tiprack = protocol.load_labware("opentrons_96_tiprack_300ul", location="2")
    tiprack2 = protocol.load_labware("opentrons_96_tiprack_300ul", location="3")

    # pipettes
    pipette_300uL = protocol.load_instrument("p300_single", mount="right", tip_racks=[tiprack, tiprack2])
    pipette_300uL.flow_rate.aspirate = 50
    pipette_300uL.flow_rate.dispense = 100


    # load data
    data = load_data()

    # commands
    # distribute monomers
    # pipette_300uL.well_bottom_clearance.dispense = 8
    # do_monomer(pipette_300uL, mon_plate['A1'], plate, data, "MA")
    # do_monomer(pipette_300uL, mon_plate['A2'], plate, data, "MMA")
    # do_monomer(pipette_300uL, mon_plate['A3'], plate, data, "St")
    # do_monomer(pipette_300uL, mon_plate['A4'], plate, data, "DMA")
    # do_monomer(pipette_300uL, mon_plate['B1'], plate, data, "isoprene")
    # do_monomer(pipette_300uL, mon_plate['B2'], plate, data, "tBuA")
    # do_monomer(pipette_300uL, mon_plate['B3'], plate, data, "Py")

    # distribute cta
    pipette_300uL.well_bottom_clearance.aspirate = 2
    pipette_300uL.well_bottom_clearance.dispense = 10
    do_cta(pipette_300uL, cta_plate['A2'], plate, data, "BTPA")
    do_cta(pipette_300uL, cta_plate['A3'], plate, data, "CPADB")
    do_cta(pipette_300uL, cta_plate['A4'], plate, data, "S")
    do_cta(pipette_300uL, cta_plate['B1'], plate, data, "D")

    # distribute cat
    pipette_300uL.well_bottom_clearance.dispense = 1
    for well in plate.wells():
        pipette_300uL.pick_up_tip()
        pipette_300uL.aspirate(55.1, cta_plate["A1"])
        pipette_300uL.dispense(55.1, well)
        pipette_300uL.mix(1, 200, well)
        pipette_300uL.drop_tip()


    protocol.set_rail_lights(False)
