# HOME PAGE

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc 
import dash_html_components as html 

import dash_bootstrap_components as dbc

#import standard layout
from dashApps.layout import header
from dashApps.layout import callbacks as layout_callbacks

layout = html.Div([
    header,
    dbc.Container(
        html.Div(className="jumbotron", children =
            html.H1("Home")
        )#Article
    ),# Container
    ])# Div


def callbacks(app):
    layout_callbacks(app)


        
#if __name__ == "__main__":
#    app.run_server(debug=True)