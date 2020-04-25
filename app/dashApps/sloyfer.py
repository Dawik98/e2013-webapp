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
from dashApps.innstillinger import settingsFile, print_settings, get_settings, get_devices

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
            html.H5('Periode'),
            dbc.DropdownMenu(label = 'Siste 6 timer', id='dropdown-område1', children=[
            dbc.DropdownMenuItem('Siste time', id='1hours'),
            dbc.DropdownMenuItem('Siste 6 timer', id='6hours'),
            dbc.DropdownMenuItem('Siste 12 timer', id='12hours'),
            dbc.DropdownMenuItem('Siste dag', id='day'),
            dbc.DropdownMenuItem('Siste uke', id='week'),
            ])
        ], width=2),
        ]),      
]),
#Ny kontainer til graf       
dbc.Container([
    #setter graf på ny linje
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
#fjerner uønsket marg fra raden.
],no_gutters=True)
]),
#Graf for tempsensorer
dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H5('Periode'),   
            dbc.DropdownMenu(label = 'Siste 6 timer', id='dropdown-område2', children=[
            dbc.DropdownMenuItem('Siste time', id='1hours_rele'),
            dbc.DropdownMenuItem('Siste 6 timer', id='6hours_rele'),
            dbc.DropdownMenuItem('Siste 12 timer', id='12hours_rele'),
            dbc.DropdownMenuItem('Siste dag', id='day_rele'),
            dbc.DropdownMenuItem('Siste uke', id='week_rele'),
            ])
        ], width=2),
        dbc.Col([
            html.H5((html.Div(id='Overskrift-Graf'))),
            dcc.Dropdown(
                    id='måle-valg',
                    options=[{'label': s,'value': s} for s in målinger_dict.keys()],
                    value='Aktiv effekt',
                ),
            ], width=5),
    ]),
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
    @app.callback([ Output('måle-valg', 'options'),
                    Output('Overskrift-Graf', 'children')],
                    [Input('refresh-dato', 'n_clicks')],
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
        allDevices=get_devices()
        devices=[]
        for key, value in allDevices.items():
            if value[0] == sløyfe_valg:
                devices.append(value[1])
        #print(devices)
        if 'powerSwitch' not in devices:
            #Returnerer tom dropdown meny
            options={'label': "",'value': ""}
            overskrift = "Ingen målerele på denne sløyfen!"
        else:
            options=[{'label': s,'value': s} for s in målinger_dict.keys()] 
            overskrift= "Måle valg, relé"
        return options, overskrift

    #Live temperatur data
    @app.callback(Output('live-graph', 'figure'),
            [Input('graph-update', 'n_intervals'),
            Input('dropdown-område1','label')],
            [State(component_id='url', component_property='pathname'),
            ])
    def update_graph_scatter(n,dropdown_område, url):
        try:  
            #Finner sløyfevalg
            ctx = dash.callback_context
            states = ctx.states
            pathname = states['url.pathname']
            sløyfe_valg = get_sløyfe_from_pathname(pathname)
            #Gjør ænsket måleområde om til tall
            if dropdown_område == "Siste time":
                offset=1
            elif dropdown_område == "Siste 6 timer": 
                offset=6
            elif dropdown_område == "Siste 12 timer": 
                offset=12
            elif dropdown_område == "Siste dag": 
                offset=24
            elif dropdown_område == "Siste uke": 
                offset=168

            #finner området som skal hentes fra databse
            til_dato_UTC = datetime.now()
            til_dato = til_dato_UTC.astimezone(pytz.timezone('Europe/Oslo'))
            fra_dato= til_dato + relativedelta(hours=-offset)
            til_dato=til_dato.strftime("%Y-%m-%d %H:%M:%S")
            fra_dato=fra_dato.strftime("%Y-%m-%d %H:%M:%S")
            # Henter inn ny data fra database
            tempData = update_tempData(sløyfe_valg, fra_dato, til_dato)
            # Dersom måle-array er tom returneres tom graf, hindrer at siden fryser
            if not tempData:
                return {
                    'data': [],
                    'layout' : go.Layout(
                        xaxis=dict(range=[fra_dato, til_dato]),
                        yaxis=dict(range=[0,120],title='Temperatur [°C]'),
                        title="Ingen målinger i valgt periode!",
                    )
                }
            else:
                # Tilordner X og Y på graf
                data=[]
                for key in tempData:
                    data.append(
                        go.Scatter(
                            y=tempData[key]['temperature'],
                            x=tempData[key]['ts'],
                            name=key,
                            mode= 'lines+markers'
                        )
                    )
                
                return {
                    'data': data,
                    'layout' : go.Layout(
                        title='Temperaturmåling',
                        showlegend=True
                    )
                }
        #Ved feilmelding skrives det til error txt fil.                                                 
        except Exception as e:
            with open('errors.txt','a') as f:
                f.write(str(e))
                f.write('\n')
    #Live målerelé graf
    @app.callback(Output('live-graph2', 'figure'),
                [Input('graph-update2', 'n_intervals'),
                Input('dropdown-område2', 'label'),
                Input('måle-valg', 'value')],
                [State(component_id='url', component_property='pathname'),
                ]) 
    #Funksjon som returnerer data som skal plottes
    def update_graph_scatter2(n,dropdown_område, måle_valg, url):
        try:
            ctx = dash.callback_context
            states = ctx.states
            pathname = states['url.pathname']
            sløyfe_valg = get_sløyfe_from_pathname(pathname)

            #Gjør ønsket måleområde om til tall
            if dropdown_område == "Siste time":
                offset=1
            elif dropdown_område == "Siste 6 timer": 
                offset=6
            elif dropdown_område == "Siste 12 timer": 
                offset=12
            elif dropdown_område == "Siste dag": 
                offset=24
            elif dropdown_område == "Siste uke": 
                offset=168
            #finner området som skal hentes fra databse
            til_dato_UTC = datetime.now()
            til_dato = til_dato_UTC.astimezone(pytz.timezone('Europe/Oslo'))
            fra_dato= til_dato + relativedelta(hours=-offset)
            fra_dato=fra_dato.strftime("%Y-%m-%d %H:%M:%S")
            #Laster inn ny data fra database
            meterData = update_meterData(sløyfe_valg,fra_dato, til_dato)
            #Tilorder data til x og y etter målevalg
            X=meterData["timeReceived"]
            Y=meterData[målinger_dict[måle_valg]]
            #Hindrer at siden fryser
            if not X:
                return {'data': [], 'layout' : go.Layout(xaxis=dict(range=[fra_dato,til_dato]),
                                                            yaxis=dict(range=[0,100],
                                                                        title=enhet_dict[måle_valg], tickangle=0,),
                                                            title="Ingen målinger i valgt periode!",
                                                            #margin={'l':100,'r':100,'t':50,'b':50},
                                                            )}
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
    #Oppdaterer knapp for måleområde til temperatur
    @app.callback(
            Output(component_id='dropdown-område1', component_property='label'),
            [Input(component_id='1hours', component_property='n_clicks'),
            Input(component_id='6hours', component_property='n_clicks'),
            Input(component_id='12hours', component_property='n_clicks'),
            Input(component_id='day', component_property='n_clicks'),
            Input(component_id='week', component_property='n_clicks'),
            ])
    def update_label(n_1hours, n_6hours, n_12hours, n_day, n_week):
        id_lookup = {'1hours':'Siste time', '6hours':'Siste 6 timer', '12hours':'Siste 12 timer', 'day':'Siste dag', 'week': 'Siste uke'}

        ctx = dash.callback_context

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        label_clicked = id_lookup[button_id]


        if (n_1hours is None and n_6hours is None and n_12hours is None and n_day is None and n_week is None) or not ctx.triggered:
            return 'Siste 6 timer'

        return label_clicked
    
    #Oppdaterer knapp for måleområde til rele
    @app.callback(
            Output(component_id='dropdown-område2', component_property='label'),
            [Input(component_id='1hours_rele', component_property='n_clicks'),
            Input(component_id='6hours_rele', component_property='n_clicks'),
            Input(component_id='12hours_rele', component_property='n_clicks'),
            Input(component_id='day_rele', component_property='n_clicks'),
            Input(component_id='week_rele', component_property='n_clicks'),
            ])
    def update_label(n_1hours, n_6hours, n_12hours, n_day, n_week):
        id_lookup = {'1hours_rele':'Siste time', '6hours_rele':'Siste 6 timer', '12hours_rele':'Siste 12 timer', 'day_rele':'Siste dag', 'week_rele': 'Siste uke'}

        ctx = dash.callback_context

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        label_clicked = id_lookup[button_id]


        if (n_1hours is None and n_6hours is None and n_12hours is None and n_day is None and n_week is None) or not ctx.triggered:
            return 'Siste 6 timer'

        return label_clicked