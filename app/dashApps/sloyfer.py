import dash
import pandas
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly
import random
import plotly.graph_objs as go
from collections import deque


#app = dash.Dash(__name__)

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
    X = deque(maxlen=20)
    X.append(1)
    Y = deque(maxlen=20)
    Y.append(1)

    @app.callback(Output('live-graph', 'figure'),
            [Input('graph-update', 'n_intervals')])
    def update_graph_scatter(n):
        X.append(X[-1]+1)
        Y.append(Y[-1]+Y[-1]*random.uniform(-0.1,0.1))

        data = plotly.graph_objs.Scatter(
                x=list(X),
                y=list(Y),
                name='Scatter',
                mode= 'lines+markers'
                )

        return {'data': [data],'layout' : go.Layout(xaxis=dict(range=[min(X),max(X)]),
                                                    yaxis=dict(range=[min(Y),max(Y)]),)}


#if __name__ == '__main__':
 #   app.run_server(debug=True)