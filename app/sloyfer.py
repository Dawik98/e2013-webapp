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
antall_målinger=5

def update_tempData(antall_målinger):
    #if  antall_målinger_pre != antall_målinger:
    #print("Kjører funksjon")
    query = "SELECT TOP {} * FROM heatTrace1 WHERE (heatTrace1.deviceType = 'tempSensor' AND heatTrace1.deviceEui = '70-b3-d5-80-a0-10-94-46') ORDER BY heatTrace1.timeReceived DESC".format(antall_målinger)
    container_name = "heatTrace1"
    items = read_from_db(container_name, query)
    ts_ht1=[]
    temp_ht1=[]
    ts_ht1UTC=[]
    for i in items:
        temp_ht1.append(i['temperature'])
    for i in items:
        ts_ht1.append(i['_ts'])
    ts_ht1UTC= pd.to_datetime(ts_ht1, unit='s')
    #ts_ht1OSLO = ts_ht1UTC.astimezone(pytz.timezone('Europe/Oslo'))
    #print(temp_ht1)
    return  ts_ht1UTC,temp_ht1

#ts_ht1UTC, temp_ht1 = update_tempData(antall_målinger)



#Powerwitch data Må gjøres modulært
"""
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


målinger_dict={"Temperatur":temp_ht1,
#"Aktiv effekt":actPwr_ht1,
}

layout = html.Div([
    html.Label('Regulerings-sløyfe'),
    dcc.Dropdown(
        id='sløyfe-valg',
        #options=[{'label': s,'value': s} for s in sløyfer_dict.keys()],
        options=[
            {'label': 'Sløyfe 1', 'value': 'ht1'},
            {'label': u'Sløyfe 2', 'value': 'ht2'},
        ],
        value='ht1'
    ),    

    html.Label('Målinger'),
    dcc.Dropdown(
        id='måle-valg',
        options=[{'label': s,'value': s} for s in målinger_dict.keys()],
        value=['Temperatur'],
        multi=True
    ),
    
    html.Label('Antall målinger'),
    dcc.Input(id='AntallMålinger', value='20', type='text'),
    
    dcc.Graph(id='live-graph', animate=False),
        dcc.Interval(
            id='graph-update',
            interval=10*1000,
            n_intervals = 1
    ),
    
])
def callbacks(app):
    
    @app.callback(Output('live-graph', 'figure'),
            [Input('graph-update', 'n_intervals'),
            Input('sløyfe-valg', 'value'),
            Input('måle-valg', 'value'),
            Input('AntallMålinger','value')
            ])

            
    def update_graph_scatter(n,sløyfe_valg,måle_valg,antall_målinger):
        """ Graf med flere målinger
        graphs = []
        if len(måle_valg)>2:
            class_choice = 'col s12 m6 l4'
        elif len(måle_valg) == 2:
            class_choice = 'col s12 m6 l6'
        else:
            class_choice = 'col s12'
        """
        try:
            #print(ts_ht1OSLO)
            #print(temp_ht1)
            ts_ht1UTC, temp_ht1 = update_tempData(antall_målinger)
            X=ts_ht1UTC[:int(antall_målinger)]
            Y=temp_ht1[:int(antall_målinger)]

            data = plotly.graph_objs.Scatter(
                    y=Y,
                    x=X,
                    name='Scatter',
                    mode= 'lines+markers'
                    )
            return {'data': [data],'layout' : go.Layout(xaxis=dict(range=[(min(X)),(max(X))]), yaxis=dict(range=[0,100]),)}
            
            #Graf med flere målinger
            """
            for valg in måle_valg:

                data = go.Scatter(
                x=list(ts_ht1),
                y=list(målinger_dict[måle_valg]),
                name='Scatter',
                fill="tozeroy",
                fillcolor="#6897bb"
                )

                graphs.append(html.Div(dcc.Graph(
                id=måle_valg,
                animate=True,
                figure={'data': [data],'layout' : go.Layout(xaxis=dict(range=[min(ts_ht1),max(ts_ht1)]),
                                                            yaxis=dict(range=[min(målinger_dict[måle_valg]),max(målinger_dict[måle_valg])]),
                                                            margin={'l':50,'r':1,'t':45,'b':1},
                                                            title='{}'.format(måle_valg))}
                ), className=class_choice))

            return graphs
            """
            """
            X=ts_ht1Ps[:-20]
            Y=actPwr_ht1[:-20]

            data = plotly.graph_objs.Scatter(
                y=Y,
                x=X,
                name='Scatter',
                mode= 'lines+markers'
                )
            return {'data': [data],'layout' : go.Layout(xaxis=dict(range=[(min(X)),(max(X))]), yaxis=dict(range=[0,100]),)}
            """
        except Exception as e:
            with open('errors.txt','a') as f:
                f.write(str(e))
                f.write('\n')                                               



#if __name__ == '__main__':
 #   app.run_server(debug=True)