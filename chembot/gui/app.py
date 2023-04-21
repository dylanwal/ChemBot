from dash import Dash, html, dcc, Output, Input
import dash
import dash_bootstrap_components as dbc

app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.DARKLY])

banner = dbc.Nav(children=[
    html.Div(
    children=[
        html.A(className="navbar-brand", children="ChemBot", href='#'),
        dbc.Nav([
                    dbc.NavItem(dbc.NavLink(page['name'], href=page["relative_path"]))
                    for page in dash.page_registry.values()
                ])
    ],
    className="container-fluid"
)

<nav class="navbar navbar-expand-lg navbar-dark bg-primary">
  <div class="container-fluid">
    <a class="navbar-brand" href="#">Navbar</a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarColor01" aria-controls="navbarColor01" aria-expanded="false" aria-label="Toggle navigation">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navbarColor01">
      <ul class="navbar-nav me-auto">
        <li class="nav-item">
          <a class="nav-link active" href="#">Home
            <span class="visually-hidden">(current)</span>
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="#">Features</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="#">Pricing</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="#">About</a>
        </li>
        <li class="nav-item dropdown">
          <a class="nav-link dropdown-toggle" data-bs-toggle="dropdown" href="#" role="button" aria-haspopup="true" aria-expanded="false">Dropdown</a>
          <div class="dropdown-menu">
            <a class="dropdown-item" href="#">Action</a>
            <a class="dropdown-item" href="#">Another action</a>
            <a class="dropdown-item" href="#">Something else here</a>
            <div class="dropdown-divider"></div>
            <a class="dropdown-item" href="#">Separated link</a>
          </div>
        </li>
      </ul>
      <form class="d-flex">
        <input class="form-control me-sm-2" type="search" placeholder="Search">
        <button class="btn btn-secondary my-2 my-sm-0" type="submit">Search</button>
      </form>
    </div>
  </div>
</nav>
# Define the banner content
# banner = html.Div(
#     children=[
#         html.H2(children='ChemBot', style={'margin-bottom': '0'}),
#         html.Div(
#         [
#                 dcc.Link(
#                     html.Button(page['name'], id='btn' + page['name'], n_clicks=0),
#                     href=page["relative_path"]
#                 )
#
#             for page in dash.page_registry.values()
#         ],
#     ),
#
#     #     html.Div(
#     #         children=[
#     #             dcc.Link(html.Button('Home', id='btn-home', n_clicks=0), href=page["relative_path"])
#     #             dcc.Link(html.Button('Page 1', id='btn-page-1', n_clicks=0),
#     #             dcc.Link(html.Button('Page 2', id='btn-page-2', n_clicks=0),
#     #         ],
#     #         style={'display': 'flex', 'justify-content': 'center'}
#     #     )
#     ],
#     className= "navbar navbar-expand-lg navbar-dark bg-primary"
#     # style={
#     #     'background-color': '--bs-blue',
#     #     'color': '#FFFFFF',
#     #     'padding': '20px',
#     #     'text-align': 'center'
#     # }
# )

app.layout = html.Div([
    banner,
    # html.Div(
    #     [
    #         html.Div(
    #             dcc.Link(
    #                 f"{page['name']} - {page['path']}", href=page["relative_path"]
    #             )
    #         )
    #         for page in dash.page_registry.values()
    #     ]
    # ),
    html.Br(),
    dash.page_container
])

# @app.callback(Output('page-content', 'children'), [Input('btn-home', 'n_clicks'), Input('btn-page-1', 'n_clicks'), Input('btn-page-2', 'n_clicks')])
# def display_page(btn_home, btn_page_1, btn_page_2):
#     ctx = dash.callback_context
#     if not ctx.triggered:
#         return html.H1('Welcome to the home page')
#     else:
#         button_id = ctx.triggered[0]['prop_id'].split('.')[0]
#         if button_id == 'btn-home':
#             return html.H1('Welcome to the home page')
#         elif button_id == 'btn-page-1':
#             return html.H1('Welcome to page 1')
#         elif button_id == 'btn-page-2':
#             return html.H1('Welcome to page 2')
#         else:
#             return html.H1('404 - Page Not Found')


if __name__ == '__main__':
    app.run_server(debug=True)
