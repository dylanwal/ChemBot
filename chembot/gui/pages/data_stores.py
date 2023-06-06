import logging
import time

from dash import Dash, html, dcc, Input, Output

from chembot.configuration import config
from chembot.gui.gui_data import IDData
from chembot.gui.gui_actions import get_equipment_registry, get_equipment_attributes
from chembot.master_controller.registry import EquipmentRegistry
from chembot.utils.serializer import from_JSON


logger = logging.getLogger(config.root_logger_name + ".gui")


def layout_data_stores(app: Dash) -> html.Div:
    data_stores = [
            dcc.Store(id=IDData.EQUIPMENT_REGISTRY, storage_type='session', data={},
                      modified_timestamp=time.time()),
            dcc.Store(id=IDData.EQUIPMENT_UPDATE, storage_type='session', data={},
                      modified_timestamp=time.time()),
            dcc.Store(id=IDData.EQUIPMENT_ATTRIBUTES, storage_type='session', data={},
                      modified_timestamp=time.time()),
        ]

    @app.callback(
        Output(IDData.EQUIPMENT_REGISTRY, "data"),
        Input(IDData.REFRESH_REGISTRY, "n_clicks")
    )
    def update_equipment_registry(_):
        logger.debug("updating equipment registry")
        return get_equipment_registry()

    @app.callback(
        Output(IDData.EQUIPMENT_ATTRIBUTES, "data"),
        Input(IDData.EQUIPMENT_REGISTRY, "data")
    )
    def update_equipment_attributes(data: dict[str, object]):
        equipment_registry: EquipmentRegistry = from_JSON(data)
        logger.debug("updating equipment attributes")
        return get_equipment_attributes(equipment_registry.equipment.keys())

    return html.Div(data_stores)
