import dash
import dash_core_components as dcc 
import dash_html_components as html 
from dash.dependencies import Input, Output, State

import dash_bootstrap_components as dbc


navbar_items = [
    dbc.NavLink("Home", href="/Home", external_link=True),
    dbc.NavLink("Sensor Data", href="/SensorData", external_link=True),
    dbc.NavLink("test1", href="/test1", external_link=True),
    dbc.NavLink("test2", href="/test2", external_link=True),
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



#header = html.Header(className='site-heaader',
#            children = html.Nav(className="navbar navbar-expand-mg navbar-dark bg-dark fixed-top",
#            children = html.Div(className="container", 
#            children = [
#                html.A("E2013", className='navbar-brand mr-4', href="/",),
#                DangerouslySetInnerHTML('''<button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarToggle" aria-controls="navbarToggle" aria-expanded="false" aria-label="Toggle navigation"><span class="navbar-toggler-icon"></span></button>'''),
#                #html.Button(children = html.Span(className="navbar-toggler-icon"), className="navbar-toogler", type="button", **{'data-toggle': "collapse", "data-target": "#navbarColor02", "aria-controls": "navbarColor02", "aria-expanded": "false", "aria-label": "Toggle navigation"},
#                #),#button
#                html.Div(className="collapse navbar-collapse", id="navbarToggle", 
#                children = html.Div(className="navbar-nav mr-auto", children=[
#                    html.A("Home", className='nav-item nav-link', href="/",),
#                    html.A("Sensor Data", className='nav-item nav-link', href="/SensorData",),
#                    html.A("test 1", className='nav-item nav-link', href="/test1/",),
#                    html.A("test 2", className='nav-item nav-link', href="/test2/",),
#            ])#Div
#            )#Div
#            ])#Div
#            )#Nav
#            )#Header