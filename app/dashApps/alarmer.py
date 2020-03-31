# HOME PAGE

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc 
import dash_html_components as html 
import dash_bootstrap_components as dbc

from datetime import datetime

from cosmosDB import read_from_db

#import standard layout
from dashApps.layout import header
from dashApps.layout import callbacks as layout_callbacks

num_of_alarms = '25'

site_title = html.Div(html.H1("Alarmer for alle sløyfer"), className="page-header") 
# TODO legg til mulighet til å velge sløyfe

def get_alarm_table(num_of_alarms):

    if (num_of_alarms != "Alle"):
        #get data where temp is <10 or >30
        query = "SELECT TOP {1} * FROM {0} WHERE {0}.deviceType = 'tempSensor' AND ({0}.temperature < 10 OR {0}.temperature > 30 ) ORDER BY {0}.timeReceived DESC".format("heatTrace1", num_of_alarms)
        abnormal_values = read_from_db('heatTrace1', query)
    else:
        #get data where temp is <10 or >30
        query = "SELECT * FROM {0} WHERE {0}.deviceType = 'tempSensor' AND ({0}.temperature < 10 OR {0}.temperature > 30 ) ORDER BY {0}.timeReceived DESC".format("heatTrace1", num_of_alarms)
        abnormal_values = read_from_db('heatTrace1', query)

    table_header = [html.Thead(html.Tr([html.Th("Tid"), html.Th("Enhetens plassering"), html.Th("Enhetens Eui"), html.Th("Verdi"),]))]
    table_rows = []
    
    for item in abnormal_values:
        time = datetime.strptime(item["timeReceived"], '%Y-%m-%d %H:%M:%S')
        time = datetime.strftime(time, '%d.%m.%Y   %H:%M')
        devicePlacement = item["devicePlacement"]
        deviceEui = item["deviceEui"]
        temperature = item["temperature"]

        row = html.Tr([html.Td(time), html.Td(devicePlacement), html.Td(deviceEui), html.Td("{} °C".format(temperature), className="scrollBarColl")])
        table_rows.append(row)
        
    table_body=[html.Tbody(table_rows)]
    return dbc.Table(table_header+table_body, bordered=True)
    
dropdown = dbc.DropdownMenu(label = num_of_alarms, id='dropdown-alarms', children=[
    dbc.DropdownMenuItem('25', id='25'),
    dbc.DropdownMenuItem('50', id='50'),
    dbc.DropdownMenuItem('100', id='100'),
    dbc.DropdownMenuItem('Alle', id='Alle'),
])

label_dropdown = html.Div("Antall al  alarmer:", className='label-dropdown')

layout = html.Div([
    dcc.Interval(id='refresh', n_intervals=0, interval=20*1000),
    header,
    dbc.Container([
        dbc.Row(dbc.Col(site_title)),
        dbc.Row(html.Div(id='table', className='tableFixHead')),
        dbc.Row([dbc.Col(label_dropdown, width='auto'), dbc.Col(dropdown)], justify='start', no_gutters=True)

    ]),# Container
    ])# Div


def callbacks(app):
    layout_callbacks(app)

    @app.callback(
        Output(component_id='table', component_property='children'),
        [Input(component_id='refresh', component_property='n_intervals'),
        Input(component_id='25', component_property='n_clicks'),
        Input(component_id='50', component_property='n_clicks'),
        Input(component_id='100', component_property='n_clicks'),
        Input(component_id='Alle', component_property='n_clicks'),
        ])
    def display_layout(n_intervals, n_25, n_50, n_100, n_Alle):

        return [get_alarm_table(num_of_alarms)]

    @app.callback(
        Output(component_id='dropdown-alarms', component_property='label'),
        [Input(component_id='25', component_property='n_clicks'),
        Input(component_id='50', component_property='n_clicks'),
        Input(component_id='100', component_property='n_clicks'),
        Input(component_id='Alle', component_property='n_clicks'),
        ])
    def display_layout(n_25, n_50, n_100, n_Alle):
        id_lookup = {'25':'25', '50':'50', '100':'100', 'Alle':'Alle'}

        ctx = dash.callback_context

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        label_clicked = id_lookup[button_id]

        global num_of_alarms

        if (n_25 is None and n_50 is None and n_100 is None and n_Alle is None) or not ctx.triggered:
        # if neither button has been clicked, return "Not selected"
            return num_of_alarms

        num_of_alarms = label_clicked
        return label_clicked

        
#if __name__ == "__main__":
#    app.run_server(debug=True)