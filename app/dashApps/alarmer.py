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

def get_alarms():
    #get data where temp is <10 or >30
    query = "SELECT * FROM {0} WHERE {0}.deviceType = 'tempSensor' AND ({0}.temperature < 10 OR {0}.temperature > 30 ) ORDER BY {0}.timeReceived DESC"
    abnormal_values = read_from_db('heatTrace1', query)
    return abnormal_values



table_header = [html.Thead(html.Tr([html.Td("Time"), html.Td("Device placement"), html.Td("Device Eui"), html.Td("Value"),]))]
table_rows = []

for item in get_alarms():
    time = item["timeReceived"]
    devicePlacement = item["devicePlacement"]
    deviceEui = item["deviceEui"]
    temperature = item["temperature"]
    row = html.Tr([html.Td(time), html.Td(devicePlacement), html.Td(deviceEui), html.Td(temperature)])
    table_rows.append(row)
    
table_body=[html.Tbody(table_rows)]

alarm_table = dbc.Table(table_header+table_body, bordered=True)


layout = html.Div([
    header,
    dbc.Container(
        alarm_table
    ),# Container
    ])# Div


def callbacks(app):
    layout_callbacks(app)


        
#if __name__ == "__main__":
#    app.run_server(debug=True)