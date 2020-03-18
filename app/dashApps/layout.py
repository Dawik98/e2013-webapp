import dash
import dash_core_components as dcc 
import dash_html_components as html 
from dash.dependencies import Input, Output, State

import dash_bootstrap_components as dbc


navbar_items = [
    dbc.NavItem(dbc.NavLink("Home", href="/Home")),
    dbc.NavLink("Sensor Data", href="/SensorData/"),
    dbc.NavLink("test1", href="/test1/"),
    dbc.NavLink("test2", href="/test2/"),
]

header = dbc.Navbar(
    dbc.Container(
        [
            dbc.NavbarBrand("E2013", href="/"),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                dbc.Nav(
                    navbar_items, navbar=True, fill=True, horizontal="start"
                ),
                id="navbar-collapse",
                navbar=True,
            ),
        ]
    ),
    className="mb-5",
    fixed="top"
)

def callbacks(app):
    # add callback for toggling the collapse on small screens
    @app.callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")],
    )
    def toggle_navbar_collapse(n, is_open):
        if n:
            return not is_open
        return is_open
