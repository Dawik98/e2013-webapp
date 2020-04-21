import dash
import pandas as pd
from dash.dependencies import Output, Input, State
import dash_core_components as dcc
import dash_html_components as html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly
import random
import pytz
import time
import plotly.graph_objs as go
from datetime import datetime
from dateutil.relativedelta import *
from collections import deque
from cosmosDB import read_from_db
from opp_temp import update_tempData
from opp_meter import update_meterData

#import standard layout
from dashApps.layout import header, update_sløyfe_callback, get_sløyfe_from_pathname
from dashApps.layout import callbacks as layout_callbacks

#Henter inn intialverider som brukes første gang koden kjøres
til_dato = datetime.now()
fra_dato= til_dato + relativedelta(hours=-6)

# ordliste som knytter sammen streng som vises i drop-down meny knyttet til streng med datanavn som 
# brukes til å hente data fra databasen 
målinger_dict={"Aktiv effekt" : "activePower",
                "Reaktiv effekt" : "reactivePower",
                "Tilsynelatende effekt": "apparentPower",
                "Aktiv energi" : "activeEnergy",
                "Tilsynelatende energi" : "apparentEnergy",
                "Reaktiv energi" : "reactiveEnergy",
                "Spenning" : "voltage",
                "Strøm" : "current",
                "Frekvens" : "frequency",
                "Kjøretid" : "runTime",              
}

#Brukes til å dynamisk skifte benemning på graf til målerelé.
enhet_dict={"Aktiv effekt" : " Aktiv effekt [W]",
            "Reaktiv effekt" : " Reaktv effekt [VAr]",
            "Tilsynelatende effekt": " Tilsynelatende effekt[VA]",
            "Aktiv energi" : "Aktiv energi [kWh]",
            "Tilsynelatende energi" : " Tilsynelatende energi [kVAh]",
            "Reaktiv energi" : " Reaktiv energi [VArh]",
            "Spenning" : " Spennning [V]",
            "Strøm" : " Strøm [mA]",
            "Frekvens" : " Nettfrekvens [f]",
            "Kjøretid" : "Kjøretid [s]", 
}

#Funksjon for å printe overskrift basert på sløyfevalg
def get_site_title(chosen_sløyfe):
    site_title = html.Div(html.H1("Trendvindu for {}".format(chosen_sløyfe), id="site-title"), className="page-header") 
    return site_title

#Defninerer hvordan siden skal se ut. Med overskrifter, menyer, grafer osv...
layout = html.Div([
    #Header lastet inn fra layout
    header,
dbc.Container(id='main-container', children = [
dbc.Container([
    #Site title genereres av funksjon
    dbc.Row([html.Div(id='site-title-div')]),
    dbc.Row([
        dbc.Col([
        html.H5('Fra dato'),
        dbc.Input(id='fra_Dato', value=fra_dato.strftime("%Y-%m-%d %H:%M:%S"), type='text',placeholder="YYYY-MM-DD HH:MM:SS",debounce=True)
        ], width=2),

        dbc.Col([
        html.H5('Til dato'),
        dbc.Input(id='til_Dato', value='', type='text',placeholder="YYYY-MM-DD HH:MM:SS, ' <Empty> ' for live",debounce=True)
        ], width=2),
    ])
    ]),
dbc.Container([
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='live-graph', animate=False),
                dcc.Interval(
                    id='graph-update',
                    #Oppdaterer hvert 15. sekund. Gri tid til å lese fra database
                    interval=15*1000,
                    n_intervals = 1
            )
      ],width={'size':12,'order':1}),
],no_gutters=True)
]),
#Graf for tempsensorer
dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H5('Måle valg, relé'),
            dcc.Dropdown(
                    id='måle-valg',
                    options=[{'label': s,'value': s} for s in målinger_dict.keys()],
                    value='Aktiv effekt',
                ),
            ], width=5)
    ])
]),
#Graf for målerele
dbc.Container([
    dbc.Row([
        dbc.Col([
                dcc.Graph(id='live-graph2', animate=False),
                                dcc.Interval(
                                    id='graph-update2',
                                    #Oppdater hvert 17. sekund, vil ikke overlappe.
                                    interval=27*1000,
                                    n_intervals = 1
                            )
                ],width={'size':12,'order':1}),
],no_gutters=True)
]),
# Skjult knapp som triggrer ved refresh av siden
# Brukes til å oppdatere dato feltene hver gang siden lastes inn
dbc.Button(id='refresh-dato', style={'display': 'none'}),
])
])


# Callbacks kjører hele tiden, og oppdater verdier som ble definert i layout. 
def callbacks(app):
    #Callbacks importert fra layout til meny og overskrift
    layout_callbacks(app)
    update_sløyfe_callback(app, [['site-title-div', get_site_title]])
    #Laster inn ny data i datofeltet som kjøres når siden lastes inn
    @app.callback(Output('fra_Dato', 'value'),
                    [Input('refresh-dato', 'n_clicks'),
                    ])
    #Funksjon for å finne nåtid
    def update_refresh(n):
        til_dato = datetime.now()
        fra_dato= til_dato + relativedelta(hours=-6)
        fra_dato=fra_dato.strftime("%Y-%m-%d %H:%M:%S")
        return fra_dato

    #Live temperatur data
    @app.callback(Output('live-graph', 'figure'),
            [Input('graph-update', 'n_intervals'),
            Input('fra_Dato', 'value'),
            Input('til_Dato','value')],
            [State(component_id='url', component_property='pathname'),
            ])
    

    def update_graph_scatter(n,fra_dato, til_dato, url):
        try:  
            #Finner sløyfevalg
            ctx = dash.callback_context
            states = ctx.states
            pathname = states['url.pathname']
            sløyfe_valg = get_sløyfe_from_pathname(pathname)
            #Dersom datofletet er tomt returnerer vi tom graf.
            #Hindrer at siden fryser
            if fra_dato == "":
                 return {'data': [], 'layout': {}}
            else:
                #henter inn ny data fra database
                ts_UTC, temp = update_tempData(sløyfe_valg, fra_dato, til_dato)
                if not temp:
                    return {'data': [], 'layout': {}}
                else:
                    #tilordner X og Y på graf
                    X=ts_UTC
                    Y=temp
                    data = plotly.graph_objs.Scatter(
                            y=Y,
                            x=X,
                            name='Scatter',
                            mode= 'lines+markers'
                            )
                    return {'data': [data],'layout' : go.Layout(xaxis=dict(range=[(min(X)),(max(X))]),
                                                                yaxis=dict(range=[0,120],title='Temperatur [°C]'),
                                                                title='Temperatur Måling',
                                                                #margin={'l':300,'r':100,'t':5,'b':50},
                                                            )}
        #Ved feilmelding skrives det til error txt fil.                                                 
        except Exception as e:
            with open('errors.txt','a') as f:
                f.write(str(e))
                f.write('\n')
    #Live målerelé graf
    @app.callback(Output('live-graph2', 'figure'),
                [Input('graph-update2', 'n_intervals'),
                Input('fra_Dato', 'value'),
                Input('til_Dato','value'),
                Input('måle-valg', 'value')],
                [State(component_id='url', component_property='pathname'),
                ]) 
    #Funksjon som returnerer data som skal plottes
    def update_graph_scatter2(n,fra_dato, til_dato, måle_valg, url):
        try:
            ctx = dash.callback_context
            states = ctx.states
            pathname = states['url.pathname']
            sløyfe_valg = get_sløyfe_from_pathname(pathname)
            #Dersom datofletet er tomt returnerer vi tom graf.
            #Hindrer at siden fryser
            if fra_dato == "":
                return {'data': [], 'layout': {}}
            else: 
                #Laster inn ny data fra database
                meterData = update_meterData(sløyfe_valg,fra_dato, til_dato)
                #Tilorder data til x og y etter målevalg
                X=meterData["timeReceived"]
                Y=meterData[målinger_dict[måle_valg]]
                if not X:
                    return {'data': [], 'layout': {}}
                else:
                    #Returnerer graf med data og layout
                    data = plotly.graph_objs.Scatter(
                            y=Y,
                            x=X,
                            name='Scatter',
                            mode= 'lines+markers'
                            )  
                    return {'data': [data],'layout' : go.Layout(xaxis=dict(range=[(min(X)),(max(X))]),
                                                                yaxis=dict(range=[(min(Y)*.95),(max(Y)*1.05)],
                                                                            title=enhet_dict[måle_valg], tickangle=0,),
                                                                title='Målerelé: {}'.format(måle_valg),
                                                                #margin={'l':100,'r':100,'t':50,'b':50},
                                                                )}                                                                                                                                                            
        except Exception as e:
            with open('errors.txt','a') as f:
                f.write(str(e))
                f.write('\n')
