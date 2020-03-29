import dash
import dash_core_components as dcc 
import dash_html_components as html 
from dash.dependencies import Input, Output, State

import dash_bootstrap_components as dbc


navbar_items = [
    dbc.NavLink("Home", href="/Home", external_link=True),
    dbc.NavLink("Sløyfer", href="/sløyfer", external_link=True),
    dbc.NavLink("Alarmer", href="/alarmer", external_link=True),
    dbc.NavLink("Innstillinger", href="/innstillinger", external_link=True),
]

header = dbc.Navbar(
    dbc.Container(
        [
            dbc.NavbarBrand("E2013", href="/", external_link=True),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                dbc.Nav(
                    navbar_items, className="mr-auto", navbar=True,
                ),
                id="navbar-collapse",
                navbar=True,
            ),
        ]),
    className="mb-5",
    color="primary",
    dark=True,
    sticky="top"
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
