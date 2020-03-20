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
from dashApps.opp_temp import update_tempData

ts_ht1=[]
temp_ht1=[]
ts_ht1UTC=[]

målinger_dict={"Aktiv effekt":temp_ht1,
#"Aktiv effekt":actPwr_ht1,
}

sløyfer_dict={"Sløyfe 1":"heatTrace1",
"Sløyfe 2":"heatTrace2",
}
"""
#Powerwitch data Må gjøres modulært
query = "SELECT * FROM heatTrace1 WHERE (heatTrace1.deviceType = 'powerSwitch' AND heatTrace1.deviceEui = '70-b3-d5-8f-f1-00-1e-78' AND heatTrace1.messageType ='powerData') ORDER BY heatTrace1.timeReceived DESC"
container_name = "heatTrace1"
items = read_from_db(container_name, query)


actPwr_ht1=[]
for i in items:
    actPwr_ht1.append(i['activePower'])

rctPwr_ht1=[]
for i in items:
    rctPwr_ht1.append(i['reactivePower'])

appPwr_ht1=[]
for i in items:
    appPwr_ht1.append(i['apparentPower'])

volt_ht1=[]
for i in items:
    volt_ht1.append(i['voltage'])
    
freq_ht1 = []
for i in items:
    freq_ht1.append(i['frequency'])

ts_ht1Ps=[]
for i in items:
    ts_ht1Ps.append(i['_ts'])
ts_ht1Ps= pd.to_datetime(ts_ht1Ps, unit='s')
"""
#print(items)

#import standard layout
from dashApps.layout import header
from dashApps.layout import callbacks as layout_callbacks


layout = html.Div([
    header,
    html.Label('Regulerings-sløyfe'),
    dcc.Dropdown(
        id='sløyfe-valg',
        options=[{'label': s,'value': s} for s in sløyfer_dict.keys()],
        value='Sløyfe 1'
    ),    

    html.Label('Antall målinger'),
    dcc.Input(id='AntallMålinger', value='60', type='text'),

    dcc.Graph(id='live-graph', animate=False),
        dcc.Interval(
            id='graph-update',
            interval=15*1000,
            n_intervals = 1
    ),
    html.Label('Målinger'),
    dcc.Dropdown(
        id='måle-valg',
        options=[{'label': s,'value': s} for s in målinger_dict.keys()],
        value=['Aktiv effekt'],
        multi=True
    ),
     dcc.Graph(
        id='basic-interactions',
        figure={
            'data': [
                {
                    'x': [1, 2, 3, 4],
                    'y': [4, 1, 3, 5],
                    'text': ['a', 'b', 'c', 'd'],
                    'customdata': ['c.a', 'c.b', 'c.c', 'c.d'],
                    'name': 'Trace 1',
                    'mode': 'markers',
                    'marker': {'size': 12}
                },
                {
                    'x': [1, 2, 3, 4],
                    'y': [9, 4, 1, 4],
                    'text': ['w', 'x', 'y', 'z'],
                    'customdata': ['c.w', 'c.x', 'c.y', 'c.z'],
                    'name': 'Trace 2',
                    'mode': 'markers',
                    'marker': {'size': 12}
                }
            ],
            'layout': {
                'clickmode': 'event+select'
            }
        }
    ),
])
def callbacks(app):
    layout_callbacks(app)

    X = deque(maxlen=20)
    X.append(1)
    Y = deque(maxlen=20)
    Y.append(1)

    @app.callback(Output('live-graph', 'figure'),
            [Input('graph-update', 'n_intervals'),
            Input('sløyfe-valg', 'value'),
            Input('AntallMålinger','value')
            ])   
    def update_graph_scatter(n,sløyfe_valg,antall_målinger):
        try:
            sløyfe_valg=sløyfer_dict[sløyfe_valg]
            print(sløyfe_valg)
            ts_UTC, temp = update_tempData(antall_målinger, sløyfe_valg)
            X=ts_UTC[:int(antall_målinger)]
            Y=temp[:int(antall_målinger)]
            data = plotly.graph_objs.Scatter(
                    y=Y,
                    x=X,
                    name='Scatter',
                    mode= 'lines+markers'
                    )
            return {'data': [data],'layout' : go.Layout(xaxis=dict(range=[(min(X)),(max(X))]),
                                                         yaxis=dict(range=[0,120]),
                                                         title='Temperatur Måling'),
                                                         'margin': {'l': 20, 'b': 20, 'r': 20, 't': 20},
                                                         }

        except Exception as e:
            with open('errors.txt','a') as f:
                f.write(str(e))
                f.write('\n')
