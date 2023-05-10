from dash import Dash, html, dcc, Output, Input, State
import dash
import dash_bootstrap_components as dbc

app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.DARKLY])

PLOTLY_LOGO = "assets/icon-research-catalysis-white.svg"

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=PLOTLY_LOGO, height="30px")),
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

app.layout = html.Div([
    navbar,
    html.Br(),
    dash.page_container
])


if __name__ == '__main__':
    app.run_server(debug=True)
