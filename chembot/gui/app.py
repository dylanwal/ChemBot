from dash import Dash, html
import dash
import dash_bootstrap_components as dbc

from chembot.gui.gui_data_actions import GUIInterface
from chembot.gui.components.navbar import create_navbar


class GUI:
    name = "GUI"

    def __init__(self, debug: bool = True):
        self.debug = debug
        self.app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.DARKLY])
        self.gui = GUIInterface(self.app)
        self.app.layout = html.Div([create_navbar(self.gui), html.Br(), dash.page_container])

    def activate(self):
        self.app.run_server(debug=self.debug)  # blocking
