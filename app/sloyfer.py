import dash
import pandas as pd
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly
import random
import pytz
import plotly.graph_objs as go
from datetime import datetime
from collections import deque
from cosmosDB import read_from_db

#app = dash.Dash(__name__)

#timeStamp1_dict={"Temeratur sensor:":}

#temp data, MÅ gjøres modulært
ts_ht1=[]
temp_ht1=[]
ts_ht1UTC=[]

query = "SELECT * FROM heatTrace1 WHERE (heatTrace1.deviceType = 'tempSensor' AND heatTrace1.deviceEui = '70-b3-d5-80-a0-10-94-46') ORDER BY heatTrace1.timeReceived DESC"
container_name = "heatTrace1"
items = read_from_db(container_name, query) 
for i in items:
    temp_ht1.append(i['temperature'])
for i in items:
     ts_ht1.append(i['_ts'])
ts_ht1UTC= pd.to_datetime(ts_ht1, unit='s')
#ts_ht1OSLO = ts_ht1UTC.astimezone(pytz.timezone('Europe/Oslo'))


målinger_dict={"Temperatur":temp_ht1
}

layout = html.Div([
    html.Label('Regulerings-sløyfe'),
    dcc.Dropdown(
        id='sløyfe-valg',
        #options=[{'label': s,'value': s} for s in sløyfer_dict.keys()],
        options=[
            {'label': 'Sløyfe 1', 'value': 'heatTrace1'},
            {'label': u'Sløyfe 2', 'value': 'ht2'},
        ],
        value='heatTrace1'
    ),    

    html.Label('Målinger'),
    dcc.Dropdown(
        id='måle-valg',
        options=[{'label': s,'value': s} for s in målinger_dict.keys()],
        value=['Temperatur'],
        multi=True
    ),
    
    html.Label('Antall målinger'),
    dcc.Input(id='AntallMålinger', value='30', type='text'),
    
    dcc.Graph(id='live-graph', animate=False),
        dcc.Interval(
            id='graph-update',
            n_intervals = 5*1000
    ),
    
])
def callbacks(app):
    @app.callback(
            [Output('ts_ht1UTC','number'),
            Output('temp_ht1', 'number')]
            [Input('sløyfe-valg', 'value')
            ])

    def update_tempData(sløyfe_valg):
        query = "SELECT TOP 100 * FROM {} WHERE ({}.deviceType = 'tempSensor' AND {}.deviceEui = '70-b3-d5-80-a0-10-94-46') ORDER BY {}.timeReceived DESC".format(sløyfe_valg)
        container_name = {}.format(sløyfe_valg)
        items = read_from_db(container_name, query) 
        items[0]['temperature']
        for i in items:
            temp_ht1.append(i['temperature'])
        for i in items:
            ts_ht1.append(i['_ts'])
            ts_ht1UTC= pd.to_datetime(ts_ht1, unit='s')
            #ts_ht1OSLO = ts_ht1UTC.astimezone(pytz.timezone('Europe/Oslo'))
        return  ts_ht1UTC,temp_ht1


   

    @app.callback(Output('live-graph', 'figure'),
            [Input('graph-update', 'n_intervals'),
            Input('ts_ht1UTC', 'value'),
            Input('temp_ht1', 'value'),
            Input('AntallMålinger','value')
            ])

         
    def update_graph_scatter(n,ts,temp,antall_målinger):
        try:
            X=ts_ht1[:int(antall_målinger)]
            Y=temp[:int(antall_målinger)]

            data = plotly.graph_objs.Scatter(
                    y=Y,
                    x=X,
                    name='Scatter',
                    mode= 'lines+markers'
                    )
            return {'data': [data],'layout' : go.Layout(xaxis=dict(range=[(min(X)),(max(X))]), yaxis=dict(range=[0,100]),)}
    
        except Exception as e:
            with open('errors.txt','a') as f:
                f.write(str(e))
                f.write('\n')                                               


