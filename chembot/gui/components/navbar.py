
from dash import Dash, html
import dash_bootstrap_components as dbc

from chembot.gui.gui_data_actions import GUIInterface


def create_navbar(gui: GUIInterface) -> html.Div:
    navbar = dbc.Navbar(
        dbc.Container(
            [
                html.A(
                    # Use row and col to control vertical alignment of logo / brand
                    dbc.Row(
                        [
                            dbc.Col(html.Img(src=gui.data.LOGO, height="30px")),
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