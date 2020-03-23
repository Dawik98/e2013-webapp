# HOME PAGE

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc 
import dash_html_components as html 

import dash_bootstrap_components as dbc

from cosmosDB import read_from_db

#import standard layout
from dashApps.layout import header
from dashApps.layout import callbacks as layout_callbacks

def get_alarm_table():
    #get data where temp is <10 or >30
    query = "SELECT * FROM {0} WHERE {0}.deviceType = 'tempSensor' AND ({0}.temperature < 10 OR {0}.temperature > 30 ) ORDER BY {0}.timeReceived DESC".format("heatTrace1")
    abnormal_values = read_from_db('heatTrace1', query)

    table_header = [html.Thead(html.Tr([html.Th("Time"), html.Th("Device placement"), html.Th("Device Eui"), html.Th("Value"),]))]
    table_rows = []
    
    for item in abnormal_values:
        time = item["timeReceived"]
        devicePlacement = item["devicePlacement"]
        deviceEui = item["deviceEui"]
        temperature = item["temperature"]
        row = html.Tr([html.Td(time), html.Td(devicePlacement), html.Td(deviceEui), html.Td("{} °C".format(temperature))])
        table_rows.append(row)
        
    table_body=[html.Tbody(table_rows)]
    
    return dbc.Table(table_header+table_body, bordered=True)
    

layout = html.Div([
    dcc.Interval(id='refresh', n_intervals=0, interval=10*1000),
    header,
    dbc.Container(
        html.Div(id='table', className='tableFixHead')
    ),# Container
    ])# Div


def callbacks(app):
    layout_callbacks(app)

    @app.callback(
        Output(component_id='table', component_property='children'),
        [Input(component_id='refresh', component_property='n_intervals')])
    def display_layout(n):
        #print(n)
        return [get_alarm_table()]

        
#if __name__ == "__main__":
#    app.run_server(debug=True)