import dash
import pandas as pd
from dash.dependencies import Output, Input, State
import dash_core_components as dcc
import dash_html_components as html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import plotly
import pytz
import plotly.graph_objs as go
from datetime import datetime
from dateutil.relativedelta import *
from collections import deque
from cosmosDB import read_from_db
from graphData import update_historiskData
from main import baseURL

#import standard layout
from dashApps.layout import header, update_sløyfe_callback, get_sløyfe_from_pathname
from dashApps.layout import callbacks as layout_callbacks
from dashApps.innstillinger import get_sløyfer, settingsFile, print_settings, get_settings

#knytter sammen string som brukes til listene med data, og synlig tekst i meny
målinger_dict={ "Temperatur" : "temperature",
                "Aktiv effekt" : "activePower",
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
enhet_dict={"Temperatur" : "[°C]",
            "Aktiv effekt" : "[W]",
            "Reaktiv effekt" : "[VAr]",
            "Tilsynelatende effekt": "[VA]",
            "Aktiv energi" : "[kWh]",
            "Tilsynelatende energi" : "[kVAh]",
            "Reaktiv energi" : "[VArh]",
            "Spenning" : "[V]",
            "Strøm" : "[mA]",
            "Frekvens" : "[f]",
            "Kjøretid" : "[s]", 
}          
#Dager måledata med 5 min samplerate
#antall_målinger = 288*1 

#Funksjon for å printe overskrift basert på sløyfevalg
def get_site_title(chosen_sløyfe):
    site_title = html.Div(html.H1("Historisk graf for {}".format(chosen_sløyfe), id="site-title"), className="page-header") 
    return site_title

#Funksjon som brukes til å laste inn historisk data
def site_refreshed ():
    til_dato_UTC = datetime.now()
    til_dato = til_dato_UTC.astimezone(pytz.timezone('Europe/Oslo'))
    fra_dato = til_dato - relativedelta(months=1)
    historiskData={}
    sløyfer=get_sløyfer()
    for i in sløyfer:
        historiskData[i] = update_historiskData(i)
    return historiskData, til_dato, fra_dato

#Laster inn midlertidig data når appen kjøres første gang. Layout er avhening av å ha ferider. 
historiskData, til_dato, fra_dato = site_refreshed()

# Definerer hvordan siden skal se ut
layout = html.Div([
    #Header lastet inn fra layout
    header,
dbc.Container([   
    dbc.Jumbotron([
        dbc.Row([
            dbc.Col([
            #Site title genereres av funksjon
            html.Div(id='site-title-div')
            ], align="center")
        ]
        ),
        dbc.Row([
            #Usynlig knapp for å plassere de andre knappene til venstre
            dbc.Col([
                    html.Div(dbc.Button("",
                    id='formateringskanpp',
                    style={'display':'none'},
                    ),
                    )
            ], width=8),
            dbc.Col([
                    html.Div(dbc.Button("Oppdater data",
                    id='trigger-refresh',
                    color="secondary"),
                    )
            ], width=2),
            dbc.Col([
                    html.Div(dbc.Button("Last ned data",
                    id='download-excel',
                    color="secondary",
                    #Setter href til noe helt annet. Slik at når kanppen trykkes lastes urlen i callack på ny fullstendig. 
                    href='/hjem/',
                    target="_blank"),
                    )
            ]),

        ]),
        # Ny rad med input felt og meny som brukes til å styre grafen
        dbc.Row([
            dbc.Col([
            html.H5('Fra dato:'),
            dbc.Input(id='fra_Dato', value=fra_dato.strftime("%Y-%m-%d %H:%M:%S"), type='text',placeholder="YYYY-MM-DD HH:MM:SS",debounce=True)
            ], width=2),

            dbc.Col([
            html.H5('Til dato:'),
            dbc.Input(id='til_Dato', value=til_dato.strftime("%Y-%m-%d %H:%M:%S"), type='text',placeholder="YYYY-MM-DD HH:MM:SS",debounce=True)
            ], width=2),

            dbc.Col([
            html.H5('Måle valg:'),
            dcc.Dropdown(id='måle-valg',
                            options=[{'label': s,'value':s} for s in målinger_dict.keys()],
                            #value='Temperatur',
                            placeholder="Velg en eller flere målinger",
                            multi=True
                            ),
            ], width=5),
        ]),
        #Setter graf på ny linje
        dbc.Row([
            dbc.Col([
                html.Div([dcc.Graph(id="my-graph")]),
            ],width={'size':12,'order':1}),
        #Fjerner uønsket marg til rad   
        ],no_gutters=True)
    ]),
], id='main-container'),
#### Tomme divs for callbacks og datalagring ########
#Bruker skjult input felt, som er avhenig av en verdi som blir oppdatert
#sammtidig som historisk data, til å trigge loading icon.
html.Div([dcc.Loading(
    id = "loading-icon",
    children=[
        dcc.Input(id='Loading-icon',style={'display':'none'})
            ],
    type="graph", fullscreen=True),
]),
#Locale storages som holder lagret data, tar for lang tid å laste inn hver gang. Overskiver intialverdiene ved start
html.Div([dcc.Store(id='historisk-data-store', storage_type='local')]),
html.Div([dcc.Store(id='til-dato-store', storage_type='local')]),
html.Div([dcc.Store(id='fra-dato-store', storage_type='local')]),
#Skjult div som holder dataen som plottes
html.Div([html.Div(id='historisk-data',children=historiskData)]),   
])  

def callbacks(app):
    #Callbacks importert fra layout til meny og overskrift
    layout_callbacks(app)
    update_sløyfe_callback(app, [['site-title-div', get_site_title]])
    # Oppdater minne
    #Refresh dato og data ved refresh side
    @app.callback([Output('historisk-data-store', 'data'),
                    Output('til-dato-store', 'data'),
                    Output('fra-dato-store', 'data'),
                    Output('loading-icon', 'value')],
                    [Input('trigger-refresh', 'n_clicks'),
                    ])
    #Bruker kanppen til å laste inn ny data. 
    def update_refreshData(n):
        if n is None:
            #Stopper for å laste inn data ved refresh av side
            raise PreventUpdate
        else:
            historiskData, til_dato, fra_dato = site_refreshed()
            til_dato=til_dato.strftime("%Y-%m-%d %H:%M:%S")
            fra_dato=fra_dato.strftime("%Y-%m-%d %H:%M:%S")
            #String i tom div som brukes til å triggre loading icon
            a="Spinn!"
            return historiskData, til_dato, fra_dato,a
    #Laster inn ny data i datofeltet som kjøres når siden lastes inn
    @app.callback([Output('måle-valg', 'options'),
                    Output('måle-valg', 'multi')],
                    [Input('trigger-refresh', 'n_clicks')],
                    [State(component_id='url', component_property='pathname'),
                    ])
    #Funksjon for å oppdatere informasjon når siden lastes
    def update_refresh(n, url):
        #Finner sløyfevalg
        ctx = dash.callback_context
        states = ctx.states
        pathname = states['url.pathname']
        sløyfe_valg = get_sløyfe_from_pathname(pathname)

        #Tømmer målevalg for rele dersom sløyfen ikke har et rele.
        settings=get_settings()
        nb_items=len(settings[sløyfe_valg]['devices'])
        devices=[]
        for i in range(0, nb_items):
            devices.append(settings[sløyfe_valg]['devices'][i]['deviceType'])
        if 'Power Switch' not in devices:
            #print("Ingen powerswitch")
            #Returnerer bare temperatur valg
            options=[{'label':"Temperatur" ,'value':"Temperatur"}]
            multi=True
            return options, multi 
        else:
            options=[{'label': s,'value':s} for s in målinger_dict.keys()] 
            multi=True
        return options, multi



    #Flytt minne til data som plottes/ vises
    @app.callback(
            [Output('historisk-data', 'children'),
            Output('til_Dato', 'value'),
            Output('fra_Dato', 'value')],
            [Input('fra-dato-store', 'data'),
            Input('til-dato-store', 'data'),
            Input('historisk-data-store', 'data')],
    )

    def update_data(fra_dato_store, til_dato_store, historiskData_store):
        #Dersom data har blitt opdatert etter koden ble lastet opp til server, brukes disse.
        if fra_dato_store != None:
            historiskData=historiskData_store
            fra_dato=fra_dato_store
            til_dato=til_dato_store
        return historiskData, til_dato, fra_dato
    #Plotter data
    @app.callback(
        dash.dependencies.Output('my-graph', 'figure'),
        [Input('fra_Dato', 'value'),
        Input('til_Dato', 'value'),
        Input('måle-valg', 'value'),
        Input('historisk-data', 'children')],
        [State(component_id='url', component_property='pathname'),
        ])

    def update_figure(fra_dato, til_dato, måle_valg, historiskData, url):
        #Henter in pathname, og finner sløyfevalg som skal plottes
        ctx = dash.callback_context
        states = ctx.states
        pathname = states['url.pathname']
        sløyfe_valg = get_sløyfe_from_pathname(pathname)
        #Plotter alle valgte målinger
        if måle_valg == None:
            return {'data': [], "layout": go.Layout(xaxis=dict(range=[fra_dato,til_dato]),
                                        title="Ingen måling valgt",
                                        #autosize=False,
                                        #width=1700,
                                        height=800,
                                        showlegend=True,
                                        paper_bgcolor="#DCDCDC",
                                        plot_bgcolor="#D3D3D3",
                                        margin=dict(l=50, r=50, t=50, b=50),
                                                        )}
        else:
            data = []
            for måling in måle_valg:
                if måling == "Temperatur":
                    for eui in historiskData[sløyfe_valg]['Temperatur-Sensor']:
                        print(eui)
                        data.append(
                            go.Scatter(
                                y=historiskData[sløyfe_valg]["Temperatur-Sensor"][eui]["temperature"],
                                x=historiskData[sløyfe_valg]["Temperatur-Sensor"][eui]["timeReceived"],
                                mode='lines+markers',
                                marker={"size": 3.5} ,
                                name="{0} {1}, {2}".format(måling, enhet_dict[måling], eui)
                            )
                        )
                if måling == "Aktiv effekt":
                    data.append(
                        go.Scatter(
                            y=historiskData[sløyfe_valg]["Power-Switch"]["activePower"],
                            x=historiskData[sløyfe_valg]["Power-Switch"]["timeReceived"],
                            mode='lines+markers',
                            marker={"size": 3.5},
                            name="{0} {1}".format(måling, enhet_dict[måling])
                        )
                    )
                if måling == "Reaktiv effekt":
                    data.append(
                        go.Scatter(
                            y=historiskData[sløyfe_valg]["Power-Switch"]["reactivePower"],
                            x=historiskData[sløyfe_valg]["Power-Switch"]["timeReceived"] ,
                            mode='lines+markers',
                            marker={"size": 3.5},
                            name="{0} {1}".format(måling, enhet_dict[måling])
                        )
                    )
                if måling == "Tilsynelatende effekt":
                    data.append(
                        go.Scatter(
                            y=historiskData[sløyfe_valg]["Power-Switch"]["apparentPower"],
                            x=historiskData[sløyfe_valg]["Power-Switch"]["timeReceived"] ,
                            mode='lines+markers',
                            marker={"size": 3.5},
                            name="{0} {1}".format(måling, enhet_dict[måling])
                        )
                    )
                if måling == "Aktiv energi":
                    data.append(
                        go.Scatter(y=historiskData[sløyfe_valg]["Power-Switch"]["activeEnergy"],
                            x=historiskData[sløyfe_valg]["Power-Switch"]["timeReceived"],
                            mode='lines+markers',
                            marker={"size": 3.5},
                            name="{0} {1}".format(måling, enhet_dict[måling])
                        )
                    )
                if måling == "Tilsynelatende energi":
                    data.append(
                        go.Scatter(y=historiskData[sløyfe_valg]["Power-Switch"]["apparentEnergy"],
                            x=historiskData[sløyfe_valg]["Power-Switch"]["timeReceived"], 
                            mode='lines+markers',
                            marker={"size": 3.5},
                            name="{0} {1}".format(måling, enhet_dict[måling])
                        )
                    )
                if måling == "Reaktiv energi":
                    data.append(
                        go.Scatter(y=historiskData[sløyfe_valg]["Power-Switch"]["reactiveEnergy"],
                            x=historiskData[sløyfe_valg]["Power-Switch"]["timeReceived"], 
                            mode='lines+markers',
                            marker={"size": 3.5},
                            name="{0} {1}".format(måling, enhet_dict[måling])
                        )
                    )
                if måling == "Spenning":
                    data.append(
                        go.Scatter(y=historiskData[sløyfe_valg]["Power-Switch"]["voltage"],
                            x=historiskData[sløyfe_valg]["Power-Switch"]["timeReceived"], 
                            mode='lines+markers',
                            marker={"size": 3.5},
                            name="{0} {1}".format(måling, enhet_dict[måling])
                        )
                    )
                if måling == "Strøm":
                    data.append(
                        go.Scatter(y=historiskData[sløyfe_valg]["Power-Switch"]["current"],
                            x=historiskData[sløyfe_valg]["Power-Switch"]["timeReceived"], 
                            mode='lines+markers',
                            marker={"size": 3.5},
                            name="{0} {1}".format(måling, enhet_dict[måling])
                        )
                    )
                if måling == "Frekvens":
                    data.append(
                        go.Scatter(y=historiskData[sløyfe_valg]["Power-Switch"]["frequency"],
                            x=historiskData[sløyfe_valg]["Power-Switch"]["timeReceived"], 
                            mode='lines+markers',
                            marker={"size": 3.5},
                            name="{0} {1}".format(måling, enhet_dict[måling])
                        )
                    )
                if måling == "Kjøretid":
                    data.append(
                        go.Scatter(y=historiskData[sløyfe_valg]["Power-Switch"]["runTime"],
                            x=historiskData[sløyfe_valg]["Power-Switch"]["timeReceived"], 
                            mode='lines+markers',
                            marker={"size": 3.5},
                            name="{0} {1}".format(måling, enhet_dict[måling])
                        )
                    )
            #Returnerer data som skal plottes, traces som ikke blir fyllt med data plottes blankt. 
            return {
                "data": data,
                "layout": go.Layout(
                    xaxis=dict(range=[fra_dato,til_dato]),
                    title="Historikk",
                    #autosize=False,
                    #width=1700,
                    height=800,
                    showlegend=True,
                    legend=dict(orientation="h"),
                    font=dict(
                    family="historikk",
                    size=18,
                    ),
                    paper_bgcolor="#DCDCDC",
                    plot_bgcolor="#D3D3D3",
                    margin=dict(l=50, r=50, t=50, b=50),
                    )}
    #åpner ny fane som redirectes til /excel-download/.... i flask appen som har funksjon for å laste ned excel fil. 
    #Url kodes også med informasjon om hva som skal lastes ned
    @app.callback(
        Output('download-excel', 'href'),
        [Input('fra_Dato', 'value'),
        Input('til_Dato', 'value')],
        [State(component_id='url', component_property='pathname'),
        ])
    def update_link(fra_dato, til_dato, url):
        #Henter in pathname, og finner sløyfevalg som skal plottes
        ctx = dash.callback_context
        states = ctx.states
        pathname = states['url.pathname']
        sløyfe_valg = get_sløyfe_from_pathname(pathname)
        return "{3}/excel-download/?value={0}/{1}/{2}".format(sløyfe_valg, fra_dato, til_dato, baseURL)