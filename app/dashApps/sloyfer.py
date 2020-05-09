import dash
from dash.dependencies import Output, Input, State
import dash_core_components as dcc
import dash_html_components as html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly
import pytz
import plotly.graph_objs as go
from datetime import datetime
from dateutil.relativedelta import *
from graphData import update_tempData, update_meterData
from dashApps.innstillinger import settingsFile, print_settings, get_settings, get_devices

# Importer standard layout
from dashApps.layout import header, update_sløyfe_callback, get_sløyfe_from_pathname
from dashApps.layout import callbacks as layout_callbacks

# Henter inn intialverider som brukes første gang koden kjøres
til_dato = datetime.now()
fra_dato= til_dato + relativedelta(hours=-6)
lastMessurement = {
    'tempMessage': '0000-01-01 00:00:00',
    'powerMessage': '0000-01-01 00:00:00'
}

# Ordliste som knytter sammen streng som vises i drop-down meny knyttet til streng med datanavn som 
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

# Brukes til å dynamisk skifte benemning på graf til målerelé.
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

# Funksjon for å printe overskrift basert på sløyfevalg
def get_site_title(chosen_sløyfe):
    site_title = html.Div(html.H1("Trendvindu for {}".format(chosen_sløyfe), id="site-title"), className="page-header") 
    return site_title

# Defninerer hvordan siden skal se ut. Med overskrifter, menyer, grafer osv...
layout = html.Div([
    # Header lastet inn fra layout
    header,
dbc.Container(id='main-container', children = [
    # Site title genereres av funksjon
    dbc.Row([html.Div(id='site-title-div')]),
    dbc.Jumbotron([
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
        # Setter graf på ny linje
        dbc.Row([
            dbc.Col([
                dcc.Graph(id='live-graph', animate=False),
                    dcc.Interval(
                        id='graph-update',
                        # Oppdaterer hvert 15. sekund. Gri tid til å lese fra database
                        interval=15*1000,
                        n_intervals = 1
                )
            ],width={'size':12,'order':1}),
    # Fjerner uønsket marg fra raden.
        ],no_gutters=True),
    ])
]),
# Graf for tempsensorer
dbc.Container([
    dbc.Jumbotron([
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
            #html.H5((html.Div(id='Overskrift-Graf, rele'))),
            html.H5('Målevalg'),
            dbc.DropdownMenu(label = "Aktiv effekt", id="måle-valg", children=[
            dbc.DropdownMenuItem("Aktiv effekt", id="activePower"),
            dbc.DropdownMenuItem("Tilsynelatende effektt", id="apparentPower"),
            dbc.DropdownMenuItem("Reaktiv effekt", id="reactivePower"),
            dbc.DropdownMenuItem("Aktiv energi", id="activeEnergy"),
            dbc.DropdownMenuItem("Tilsynelatende energi", id="apparentEnergy"),
            dbc.DropdownMenuItem("Reaktiv energi", id="reactiveEnergy"),
            dbc.DropdownMenuItem('Spenning', id='voltage'),
            dbc.DropdownMenuItem('Strøm', id='current'),
            dbc.DropdownMenuItem('Frekvens', id='frequency'),
            ])
            ], width=5),
    ]),
# Graf for målerele
    dbc.Row([
        dbc.Col([
                dcc.Graph(id='live-graph2', animate=False),
                                dcc.Interval(
                                    id='graph-update2',
                                    # Oppdater hvert 27. sekund, vil ikke overlappe.
                                    interval=27*1000,
                                    n_intervals = 1
                            )
                ],width={'size':12,'order':1}),
        ],no_gutters=True)
    ]),
]),

# Skjult knapp som triggrer ved refresh av siden
# Brukes til å oppdatere dato feltene hver gang siden lastes inn
dbc.Button(id='refresh-dato', style={'display': 'none'}),
])


# Callbacks kjører hele tiden, og oppdater verdier som ble definert i layout. 
def callbacks(app):
    # Callbacks importert fra layout til meny og overskrift
    layout_callbacks(app)
    update_sløyfe_callback(app, [['site-title-div', get_site_title]])
    # Laster inn ny data i datofeltet som kjøres når siden lastes inn
    @app.callback([Output('Overskrift-Graf', 'children')],
                    [Input('refresh-dato', 'n_clicks')],
                    [State(component_id='url', component_property='pathname'),
                    ])
    # Funksjon for å oppdatere informasjon når siden lastes
    def update_refresh(n, url):
        #Finner sløyfevalg
        ctx = dash.callback_context
        states = ctx.states
        pathname = states['url.pathname']
        sløyfe_valg = get_sløyfe_from_pathname(pathname)

        # Tømmer målevalg for rele dersom sløyfen ikke har et rele.
        allDevices=get_devices()
        devices=[]
        for key, value in allDevices.items():
            if value[0] == sløyfe_valg:
                devices.append(value[1])
        if 'powerSwitch' not in devices:
            # Returnerer tom dropdown meny
            #options="Ingen målerele"
            overskrift = "Ingen målerele på denne sløyfen!"
        #else:
            #options=[{'label': s,'value': s} for s in målinger_dict.keys()] 
            #overskrift= "Måle valg"
            return overskrift

    # Live temperatur data
    @app.callback(Output('live-graph', 'figure'),
            [Input('graph-update', 'n_intervals'),
            Input('dropdown-område1','label')],
            [State(component_id='url', component_property='pathname'),
            ])
    def update_graph_scatter(n,dropdown_område, url):
        try:  
            # Finner sløyfevalg
            ctx = dash.callback_context
            states = ctx.states
            pathname = states['url.pathname']
            sløyfe_valg = get_sløyfe_from_pathname(pathname)
            # Gjør ønsket måleområde om til tall
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
            # Kontrollerer om det er innhold i mottatt data, begynner med antagelsen at listen er tom.
            empthy = True
            for eui in tempData:
                if tempData[eui]['temperature']:
                    empthy = False
                    break
            # Dersom måle-array er tom returneres tom graf, hindrer at siden fryser
            if empthy:
                return {
                    'data': [],
                    'layout' : go.Layout(
                        xaxis=dict(range=[fra_dato, til_dato]),
                        yaxis=dict(range=[0,120], title='Temperatur [°C]'),
                        title="Ingen målinger i valgt periode!",
                        paper_bgcolor="#DCDCDC",
                        plot_bgcolor="#D3D3D3",
                        margin=dict(l=60, r=5, t=60, b=20),
                    )
                }
            else:
                # Sjekker om det har kommet inn ny melding ved å sammenligne 'timeReceived' i nyeste melding
                # Detekterer samtidig laveste og høyeste temperatur som skal vises for å bestemme akser.
                lastReceiveTimes = []
                lowestTemps = []
                highestTemps =[]
                for eui in tempData:
                    if tempData[eui]['temperature']:
                        lastReceiveTimes.append(tempData[eui]['timeReceived'][0])
                        lowestTemps.append(min(tempData[eui]['temperature']))
                        highestTemps.append(max(tempData[eui]['temperature']))
                lastReceiveTime = max(lastReceiveTimes)
                lowestTemp = min(lowestTemps)
                highestTemp = max(highestTemps)
                trigger = dash.callback_context.triggered[0]['prop_id']
                if ((lastReceiveTime == lastMessurement['tempMessage']) and trigger == 'graph-update.n_intervals'):
                    return dash.dash.no_update
                else:
                    
                    # Sjekker om det har kommet inn ny melding ved å sammenligne 'timeReceived' i nyeste melding
                    # Detekterer samtidig laveste og høyeste temperatur som skal vises for å bestemme akser.
                    lastReceiveTimes = []
                    lowestTemps = []
                    highestTemps =[]
                    for eui in tempData:
                        if tempData[eui]['temperature']:
                            lastReceiveTimes.append(tempData[eui]['timeReceived'][0])
                            lowestTemps.append(min(tempData[eui]['temperature']))
                            highestTemps.append(max(tempData[eui]['temperature']))
                    lastReceiveTime = max(lastReceiveTimes)
                    lowestTemp = min(lowestTemps)
                    highestTemp = max(highestTemps)

                    trigger = dash.callback_context.triggered[0]['prop_id']
                    if ((lastReceiveTime == lastMessurement['tempMessage']) and trigger == 'graph-update.n_intervals'):
                        return dash.dash.no_update
                    else:
                        lastMessurement['tempMessage'] = lastReceiveTime
                    # Tilordner X og Y på graf
                    
                    data=[]
                    for eui in tempData:
                        if tempData[eui]['temperature']:
                            data.append(
                                go.Scatter(
                                    y=tempData[eui]['temperature'],
                                    x=tempData[eui]['timeReceived'],
                                    name=eui,
                                    mode= 'lines+markers'
                                )
                            )
                    return {
                        'data': data,
                        'layout' : go.Layout(
                            yaxis=dict(range=[(lowestTemp - 10),(highestTemp + 10)], title='Temperatur [°C]'),
                            title='Temperaturmåling',
                            #showlegend=True,
                            legend=dict(orientation="h",y=-0.15),
                            font=dict(
                            family="historikk",
                            size=18,
                            ),
                            paper_bgcolor="#DCDCDC",
                            plot_bgcolor="#D3D3D3",
                            margin=dict(l=60, r=5, t=35, b=25),
                            )
                    }
        # Ved feilmelding skrives det til error txt fil.                                                 
        except Exception as e:
            with open('errors.txt','a') as f:
                f.write(str(e))
                f.write('\n')
    # Live målerelé graf
    @app.callback(Output('live-graph2', 'figure'),
                [Input('graph-update2', 'n_intervals'),
                Input('dropdown-område2', 'label'),
                Input('måle-valg', 'label')],
                [State(component_id='url', component_property='pathname'),
                ]) 
    # Funksjon som returnerer data som skal plottes
    def update_graph_scatter2(n,dropdown_område, måle_valg, url):
        try:
            ctx = dash.callback_context
            states = ctx.states
            pathname = states['url.pathname']
            sløyfe_valg = get_sløyfe_from_pathname(pathname)

            # Gjør ønsket måleområde om til tall
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
            # Finner området som skal hentes fra database
            til_dato_UTC = datetime.now()
            til_dato = til_dato_UTC.astimezone(pytz.timezone('Europe/Oslo'))
            fra_dato= til_dato + relativedelta(hours=-offset)
            til_dato=til_dato.strftime("%Y-%m-%d %H:%M:%S")
            fra_dato=fra_dato.strftime("%Y-%m-%d %H:%M:%S")

            # Laster inn ny data fra database
            meterData = update_meterData(sløyfe_valg, fra_dato, til_dato)
            # Tilorder data til x og y etter målevalg
            X = meterData["timeReceived"]
            Y = meterData[målinger_dict[måle_valg]]
            # Hindrer at siden fryser
            if not X:
                allDevices=get_devices()
                devices=[]
                for key, value in allDevices.items():
                    if value[0] == sløyfe_valg:
                     devices.append(value[1])
                if 'powerSwitch' not in devices:
                    return {
                        'data': [],
                        'layout': go.Layout(
                            xaxis=dict(range=[fra_dato,til_dato]),
                            yaxis=dict(range=[0, 100],
                            title=enhet_dict[måle_valg], tickangle=0,),
                            title="Ingen målerele på denne sløyfen!",
                            paper_bgcolor="#DCDCDC",
                            plot_bgcolor="#D3D3D3",
                            margin=dict(l=60, r=5, t=60, b=20),
                        )
                    }
                else:
                    return {
                        'data': [],
                        'layout': go.Layout(
                            xaxis=dict(range=[fra_dato,til_dato]),
                            yaxis=dict(range=[0, 100],
                            title=enhet_dict[måle_valg], tickangle=0,),
                            title="Ingen målinger i valgt periode!",
                            paper_bgcolor="#DCDCDC",
                            plot_bgcolor="#D3D3D3",
                            margin=dict(l=60, r=5, t=60, b=20),
                        )
                    }
            else:
                # Sjekker om det har kommet inn ny melding ved å sammenligne 'timeReceived' i nyeste melding
                # Dersom callback-en ble trigget av interval-komponent og det ikke har kommet inn nye målinger skal ikke grafen oppdateres
                trigger = dash.callback_context.triggered[0]['prop_id']
                global lastMessurement
                if ((X[0] == lastMessurement['powerMessage']) and (trigger == 'graph-update2.n_intervals')):
                    return dash.dash.no_update
                else:
                    lastMessurement['powerMessage'] = X[0]
                # Returnerer graf med data og layout
                data = plotly.graph_objs.Scatter(
                    y=Y,
                    x=X,
                    name='Scatter',
                    mode= 'lines+markers'
                )  
                return {
                    'data': [data],
                    'layout' : go.Layout(
                        xaxis=dict(range=[(min(X)),(max(X))]),
                        yaxis=dict(range=[(min(Y)*.95),(max(Y)*1.05)],
                        title=enhet_dict[måle_valg], tickangle=0,),
                        title='Målerelé: {}'.format(måle_valg),
                        legend=dict(orientation="h"),
                        font=dict(
                        family="historikk",
                        size=18,
                        ),
                        paper_bgcolor="#DCDCDC",
                        plot_bgcolor="#D3D3D3",
                        margin=dict(l=60, r=5, t=35, b=25),
                    )}                                                                                                                                                            
        except Exception as e:
            with open('errors.txt','a') as f:
                f.write(str(e))
                f.write('\n')
    # Oppdaterer knapp for måleområde til temperatur
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
    
    # Oppdaterer knapp for måleområde til rele
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

    # Oppdaterer knapp for målevalg
    @app.callback(
            Output(component_id='måle-valg', component_property='label'),
            [Input(component_id="activePower", component_property='n_clicks'),
            Input(component_id="reactivePower", component_property='n_clicks'),
            Input(component_id='apparentPower', component_property='n_clicks'),
            Input(component_id='activeEnergy', component_property='n_clicks'),
            Input(component_id='apparentEnergy', component_property='n_clicks'),
            Input(component_id='reactiveEnergy', component_property='n_clicks'),
            Input(component_id='voltage', component_property='n_clicks'),
            Input(component_id='current', component_property='n_clicks'),
            Input(component_id='frequency', component_property='n_clicks'),
            ])
    def update_label(activePower, reactivePower, apparentPower, activeEnergy, apparentEnergy, reactiveEnergy, voltage, current, frequency):
        id_lookup = {"activePower":"Aktiv effekt", "reactivePower":"Reaktiv effekt",
        "apparentPower":"Tilsynelatende effekt", "activeEnergy":"Aktiv energi", "apparentEnergy": "Tilsynelatende energi","reactiveEnergy":"Reaktiv energi",
        "voltage": "Spenning","current":"Strøm","frequency": "Frekvens"}

        ctx = dash.callback_context

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        label_clicked = id_lookup[button_id]

        if (activePower is None and reactivePower is None and apparentPower is None and activeEnergy is None and apparentEnergy is None and reactiveEnergy is None and voltage is None and current is None and frequency is None) or not ctx.triggered:
            return 'Aktiv effekt'

        return label_clicked