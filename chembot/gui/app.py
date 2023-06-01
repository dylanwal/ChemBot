import logging

from dash import Dash, html
import dash
import dash_bootstrap_components as dbc

from chembot.configuration import config
from chembot.gui.gui_data import GUIData
from chembot.rabbitmq.rabbit_http import create_queue, create_binding, delete_queue

# pages
from chembot.gui.pages.navbar import layout_navbar
from chembot.gui.pages.data_stores import layout_data_stores
from chembot.gui.pages.home import layout_home
from chembot.gui.pages.rabbitmq import layout_rabbit
from chembot.gui.pages.jobs import layout_jobs

logger = logging.getLogger(config.root_logger_name + ".gui")


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
        self.app.layout = html.Div(
            [
                layout_navbar(self.app),
                layout_data_stores(self.app),
                dash.page_container
            ]
        )

        # individual pages
        dash.register_page("home", path='/', layout=layout_home(self.app))
        dash.register_page("rabbitmq", path='/rabbitmq', layout=layout_rabbit(self.app))
        dash.register_page("jobs", path='/jobs', layout=layout_jobs(self.app))
