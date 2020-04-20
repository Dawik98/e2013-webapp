import dash
import pandas as pd
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly
import random
import pytz
import plotly.graph_objs as go
import dash_daq as daq
from datetime import datetime
from collections import deque
from cosmosDB import read_from_db, connect_to_db
from opp_temp import update_tempData

sløyfer_dict={"Sløyfe 1":"heatTrace1",
              #"Sløyfe 2":"heatTrace2",
}

setpoint='20'
tilkobledeSløyfer=2
AntallSløyfer=3

layout = html.Div([
html.Div([
    html.Label('Sløyfe valg'),
    dcc.Dropdown(
        id='sløyfe-valg',
        options=[{'label': s,'value': s} for s in sløyfer_dict.keys()],
        value='Sløyfe 1'
    ),  
]),

html.Div([
daq.Indicator(
    id='DB-indicator',
    label="Connected",
)]),

html.Div([
daq.Thermometer(
        id='my-thermometer',
        labelPosition='top',
        min=0,
        max=120,
        style={
            'margin-bottom': '5%',
            'margin-top': '5%'},
        showCurrentValue=True,
        units="[°C]",
        scale={'start': 0, 'interval':10, 'custom': {setpoint: 'Referanse'}} 
        )
]),

html.Div([
    daq.Gauge(
        id='Aktive-sløyfer',
        label="Default",
        color={"gradient":True,"ranges":{"green":[2,2],"yellow":[1,1],"red":[0,0]}},
        value=tilkobledeSløyfer,
        max=2,
        min=0,
    )
 
]),

])


def callbacks(app):
    
    @app.callback([Output('DB-indicator', 'label'),
                    Output('DB-indicator', 'value'),
                    Output('DB-indicator', 'color')],
                    [Input('sløyfe-valg', 'value')])

    def db_connection(x):
        
        cosmos = connect_to_db()
        print(cosmos)

        if cosmos != "":
            value=True
            label='connected'
            color="#32CD32"   
        else:
            value=False
            label='Disconnected'
            color="#FF0000"
        return label, value, color

    @app.callback([Output('my-thermometer', 'value'),
                    Output('my-thermometer','label')],
                    [Input('sløyfe-valg', 'value')])

    def up_thermometer(sløyfe_valg):
        antall_målinger=1
        ts_UTC, temp = update_tempData(antall_målinger, sløyfer_dict[sløyfe_valg])
        label='Temperatur i {0}'.format(sløyfe_valg)
        return temp[0], label

    """   
    @app.callback([Output('Aktive-sløyfer', 'color')],
                    [Input('sløyfe-valg', 'value')])

    def up_gauge(sløyfer_aktiv):
        tilkobledeSløyfer=2
        AntallSløyfer=3

        if tilkobledeSløyfer == AntallSløyfer:
            color="#32CD32"
        elif tilkobledeSløyfer < AntallSløyfer:
            color="#ffff00"
        elif tilkobledeSløyfer == 0 :
            color="#FF0000"
        
        else: color="#FF0000" 

        return color
    """