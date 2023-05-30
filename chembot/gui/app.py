import logging
import time

from dash import Dash, html, dcc, Input, Output
import dash
import dash_bootstrap_components as dbc

from chembot.configuration import config
from chembot.gui.gui_data import GUIData, IDDataStore
from chembot.gui.gui_actions import get_equipment_registry, get_equipment_update
from chembot.rabbitmq.rabbit_http import create_queue, create_binding, delete_queue
from chembot.master_controller.registry import EquipmentRegistry
from chembot.utils.serializer import from_JSON

# pages
from chembot.gui.pages.home import layout_home
from chembot.gui.pages.rabbitmq import layout_rabbit
from chembot.gui.pages.jobs import layout_jobs

logger = logging.getLogger(config.root_logger_name + ".gui")


def create_navbar(app: Dash) -> html.Div:
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

    # add data store
    data_stores = html.Div(
        [
            dcc.Store(id=IDDataStore.EQUIPMENT_REGISTRY, storage_type='session', data={},
                      modified_timestamp=time.time()),
            dcc.Store(id=IDDataStore.EQUIPMENT_UPDATE, storage_type='session', data={},
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

    return html.Div([navbar, html.Br(), data_stores])


class GUI:
    name = GUIData.name

    def __init__(self, debug: bool = True):
        self.debug = debug
        self.app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.DARKLY])
        self._register_pages()

    def __enter__(self):
        self._create_rabbitmq_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close_rabbitmq_connection()

    def _create_rabbitmq_connection(self):
        create_queue(self.name)
        create_binding(self.name, config.rabbit_exchange)

    def _close_rabbitmq_connection(self):
        delete_queue(self.name)

    def activate(self):
        self.app.run_server(debug=self.debug)  # blocking

    def _register_pages(self):
        # layout common to all pages
        self.app.layout = html.Div([create_navbar(self.app), html.Br(), dash.page_container])

        # individual pages
        dash.register_page("home", path='/', layout=layout_home(self.app))
        dash.register_page("rabbitmq", path='/rabbitmq', layout=layout_rabbit(self.app))
        dash.register_page("jobs", path='/jobs', layout=layout_jobs(self.app))
