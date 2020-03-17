import dash
import pandas
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
#temp_ht1.reverse()
#ts_ht1.reverse()
print(temp_ht1)


#Powerwitch data
query = "SELECT * FROM heatTrace1 WHERE heatTrace1.deviceType = 'powerSwitch' ORDER BY heatTrace1.timeReceived DESC"
container_name = "heatTrace1"
items = read_from_db(container_name, query)
actEnergy_ht1 = items[0]['activeEnergy']
rctEnergy_ht1 = items[0]['reactiveEnergy']
appEnergy_ht1 = items[0]['apparentEnergy']
volt_ht1 = items[0]['voltage']
freq_ht1 = items[0]['frequency']


layout = html.Div([
    html.Label('Regulerings-sløyfe'),
    dcc.Dropdown(
        options=[
            {'label': 'Sløyfe 1', 'value': 's1'},
            {'label': u'Sløyfe 2', 'value': 's2'},
        ],
        value='s1'
    ),

    html.Label('Målinger'),
    dcc.Dropdown(
        options=[
            {'label': 'Temperatur', 'value': 'temp'},
            {'label': u'Jordfeil', 'value': 'jordfeil'},
            {'label': 'Aktiv effekt', 'value': 'aktiv_effekt'}
        ],
        value=['temp', 'aktiv_effekt'],
        multi=True
    ),
    dcc.Graph(id='live-graph', animate=True),
        dcc.Interval(
            id='graph-update',
            interval=1000,
            n_intervals = 1
        ),
   
]
)

def callbacks(app):
    
    @app.callback(Output('live-graph', 'figure'),
            [Input('graph-update', 'n_intervals'),
            ])
            
    def update_graph_scatter(n):
        try:
            X=ts_ht1[:-20]
            Y=temp_ht1[:-20]

            data = plotly.graph_objs.Scatter(
                y=Y,
                x=X,
                name='Scatter',
                mode= 'lines+markers'
                )

            return {'data': [data],'layout' : go.Layout(xaxis=dict(range=[min(X),max(X)]),
                                                    yaxis=dict(range=[min(Y),max(Y)]),)}
      
     
        except Exception as e:
            with open('errors.txt','a') as f:
                f.write(str(e))
                f.write('\n')                                               



#if __name__ == '__main__':
 #   app.run_server(debug=True)