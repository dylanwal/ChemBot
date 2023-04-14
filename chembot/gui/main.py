from dash import Dash, html, dcc
from dash.dependencies import Input, Output, State

app = Dash("chembot", assets_folder=r"gui\assets")

# load layouts
app.layout = html.Div([
    html.H1('ChemBot'),
    dcc.Tabs(id="tabs", value='tab-1', children=[
        dcc.Tab(label='Tab 1', value='tab-1'),
        dcc.Tab(label='Tab 2', value='tab-2'),
        dcc.Tab(label='Tab 3', value='tab-3'),
    ]),
    html.Div(id='tabs-content')
])

# load tab layouts
from chembot.gui.tabs.tab1_layout import tab1_layout
from chembot.gui.tabs.tab2_layout import tab2_layout
from chembot.gui.tabs.tab3_layout import tab3_layout


# tab callback
@app.callback(Output('tabs-content', 'children'),
              Input('tabs', 'value'))
def render_content(tab):
    if tab == 'tab-1':
        return tab1_layout
    elif tab == 'tab-2':
        return tab2_layout
    elif tab == 'tab-3':
        return tab3_layout


# load callbacks
from chembot.gui.tabs.tab1_callback import *


if __name__ == '__main__':
    app.run_server(debug=True)
