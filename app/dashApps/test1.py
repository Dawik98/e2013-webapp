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
        html.Article(className="jumbotron", children =
        html.Div(className="media-body", children=[
            dcc.Input(id='input', value='Enter something', type='text'),
            html.Div(id='output'),
        ])#Div
        )#Article
    ),# Container
    ])# Div


def callbacks(app):

    layout_callbacks(app)

    @app.callback(
        Output(component_id='output', component_property='children'),
        [Input(component_id='input', component_property='value')]
    )
    def update_value(input_data):
        try:
            return str(float(input_data)**2)
        except:
            return "Some error"

        
#if __name__ == "__main__":
#    app.run_server(debug=True)