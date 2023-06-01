import logging

from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc

from chembot.configuration import config
from chembot.gui.gui_data import GUIData, IDData

logger = logging.getLogger(config.root_logger_name + ".gui")


def layout_navbar(app: Dash) -> html.Div:
    navbar = dbc.Row(
        [
            dbc.Col(dbc.Navbar(
                dbc.Container(
                    [
                        html.A(
                            dbc.Row(
                                [
                                    dbc.Col(html.Img(src=GUIData.LOGO, height="30px")),
                                    dbc.Col(dbc.NavbarBrand(GUIData.navbar_title, className="ms-2")),
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
            dbc.Col(dbc.Button("refresh equipment data", id=IDData.REFRESH_REGISTRY, color="primary", className="me-1"),
                    width=2)
        ])

    return html.Div([navbar, html.Br()])
