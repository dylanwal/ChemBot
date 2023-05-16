import logging

from dash import Dash, html, dcc
import dash
import dash_bootstrap_components as dbc

from chembot.configuration import config
from chembot.gui.gui_data_actions import GUIData
from chembot.gui.pages.home import layout_home
from chembot.gui.pages.rabbitmq import layout_rabbit

logger = logging.getLogger(config.root_logger_name + ".gui")


def create_navbar() -> html.Div:
    navbar = dbc.Navbar(
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
                            )
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
    )

    return html.Div([navbar, html.Br()])


class IDGUI:
    EQUIPMENT_REGISTRY = "e"


class GUI:
    name = "GUI"

    def __init__(self, debug: bool = True):
        self.debug = debug
        self.app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.DARKLY])
        self._register_pages()

    def activate(self):
        self.app.run_server(debug=self.debug)  # blocking

    def _register_pages(self):
        # layout common to all pages
        self.app.layout = html.Div([create_navbar(), html.Br(), dash.page_container])

        # individual pages
        dash.register_page("home", path='/', layout=layout_home(self.app))
        dash.register_page("rabbitmq", path='/rabbitmq', layout=layout_rabbit(self.app))
