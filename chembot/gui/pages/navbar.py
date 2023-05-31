import logging
import time

from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc

from chembot.configuration import config
from chembot.gui.gui_data import GUIData, IDDataStore
from chembot.gui.gui_actions import get_equipment_registry, get_equipment_attributes
from chembot.master_controller.registry import EquipmentRegistry
from chembot.utils.serializer import from_JSON


logger = logging.getLogger(config.root_logger_name + ".gui")


def layout_navbar(app: Dash) -> html.Div:
    navbar = dbc.Row(
        [
            dbc.Col(dbc.Navbar(
                dbc.Container(
                    [
                        html.A(
                            # Use row and col to control vertical alignment of logo / brand
                            dbc.Row(
                                [
                                    dbc.Col(html.Img(src=GUIData.LOGO, height="30px")),
                                    dbc.Col(dbc.NavbarBrand("ChemBot", className="ms-2")),
                                    dbc.Col(
                                        dbc.Nav([
                                            dbc.NavItem(dbc.NavLink("Home", href="/")),
                                            dbc.NavItem(dbc.NavLink("Jobs", href="/jobs")),
                                            dbc.NavItem(dbc.NavLink("Rabbitmq", href="/rabbitmq")),
                                        ])
                                    ),

                                ],
                                align="center",
                                className="g-0",
                            ),
                            href="/",
                            style={"textDecoration": "none"},
                        ),

                    ]
                ),
                color="dark",
                dark=True,
            )),
            dbc.Col(dbc.Button("refresh equipment data", id="refresh_data_button", color="primary", className="me-1"),
                    width=2)
        ])

    ###################################################################################################################
    ###################################################################################################################
    # add data store
    data_stores = html.Div(
        [
            dcc.Store(id=IDDataStore.EQUIPMENT_REGISTRY, storage_type='session', data={},
                      modified_timestamp=time.time()),
            dcc.Store(id=IDDataStore.EQUIPMENT_UPDATE, storage_type='session', data={},
                      modified_timestamp=time.time()),
            dcc.Store(id=IDDataStore.EQUIPMENT_ATTRIBUTES, storage_type='session', data={},
                      modified_timestamp=time.time()),
        ]
    )

    @app.callback(
        Output(IDDataStore.EQUIPMENT_REGISTRY, "data"),
        Input("refresh_data_button", "n_clicks")
    )
    def update_equipment_registry(_):
        logger.debug("updating equipment registry")
        return get_equipment_registry()

    @app.callback(
        Output(IDDataStore.EQUIPMENT_ATTRIBUTES, "data"),
        Input(IDDataStore.EQUIPMENT_REGISTRY, "data")
    )
    def update_equipment_attributes(data: dict[str, object]):
        equipment_registry: EquipmentRegistry = from_JSON(data)
        logger.debug("updating equipment attributes")
        return get_equipment_attributes(equipment_registry.equipment.keys())

    return html.Div([navbar, html.Br(), data_stores])
