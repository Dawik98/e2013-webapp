import dash
import pandas as pd
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly
import random
import plotly.graph_objs as go
from collections import deque
from cosmosDB import read_from_db



#app = dash.Dash(__name__)

#temp data
query = "SELECT * FROM heatTrace1 WHERE (heatTrace1.deviceType = 'tempSensor' AND heatTrace1.deviceEui = '70-b3-d5-80-a0-10-94-46') ORDER BY heatTrace1.timeReceived DESC"
container_name = "heatTrace1"
items = read_from_db(container_name, query)
temp_ht1=[]
for i in items:
    temp_ht1.append(i['temperature'])
ts_ht1=[]
for i in items:
    ts_ht1.append(i['_ts'])
ts_ht1= pd.to_datetime(ts_ht1, unit='s')

#print(temp_ht1)


#Powerwitch data
query = "SELECT * FROM heatTrace1 WHERE (heatTrace1.deviceType = 'powerSwitch' AND heatTrace1.deviceEui = '70-b3-d5-8f-f1-00-1e-78' AND heatTrace1.messageType ='powerData') ORDER BY heatTrace1.timeReceived DESC"
container_name = "heatTrace1"
items = read_from_db(container_name, query)
print(items)

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
ts_ht1Ps= pd.to_datetime(ts_ht1, unit='s')

layout = html.Div([
    html.Label('Regulerings-sløyfe'),
    dcc.Dropdown(
        id='sløyfe-valg',
        options=[
            {'label': 'Sløyfe 1', 'value': 'ht1'},
            {'label': u'Sløyfe 2', 'value': 'ht2'},
        ],
        value='ht1'
    ),    

    html.Label('Målinger'),
    dcc.Dropdown(
        id='måle-valg',
        options=[
            {'label': 'Temperatur', 'value': 'temp'},
            {'label': u'Jordfeil', 'value': 'jordfeil'},
            {'label': 'Aktiv effekt', 'value': 'aktiv_effekt'},
        ],
        value=['temp'],
        #multi=True
    ),
    dcc.Graph(id='live-graph', animate=True),
        dcc.Interval(
            id='graph-update',
            interval=1000,
            n_intervals = 1
        ),
])

def callbacks(app):
    
    @app.callback(Output('live-graph', 'figure'),
            [Input('graph-update', 'n_intervals'),
            Input('sløyfe-valg', 'value'),
            Input('måle-valg', 'value')
            ])

            
    def update_graph_scatter(n,sløyfe_valg,måle_valg):
        try:
            
            X=ts_ht1[:-20]
            Y=temp_ht1[:-20]

            data = plotly.graph_objs.Scatter(
                y=Y,
                x=X,
                name='Scatter',
                mode= 'lines+markers'
                )
            """
            X=ts_ht1Ps[:-20]
            Y=actPwr_ht1[:-20]

            data = plotly.graph_objs.Scatter(
                y=Y,
                x=X,
                name='Scatter',
                mode= 'lines+markers'
                )
            """
            return {'data': [data],'layout' : go.Layout(xaxis=dict(range=[min(X),max(X)]),
                                                    yaxis=dict(range=[min(Y),max(Y)]),)}
    
     
        except Exception as e:
            with open('errors.txt','a') as f:
                f.write(str(e))
                f.write('\n')                                               



#if __name__ == '__main__':
 #   app.run_server(debug=True)