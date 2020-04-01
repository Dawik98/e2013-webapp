import dash
import pandas as pd
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
from collections import deque
from cosmosDB import read_from_db
from historie_data import update_historiskData

#import standard layout
from dashApps.layout import header, update_sløyfe_callback, get_sløyfe_from_pathname, get_sløyfer
from dashApps.layout import callbacks as layout_callbacks

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
            "Kjøretid" : "s", 
}          
#Dager måledata med 5 min samplerate
#antall_målinger = 288*1 

def get_site_title(chosen_sløyfe):
    site_title = html.Div(html.H1("Historisk graf for {}".format(chosen_sløyfe), id="site-title"), className="page-header") 
    return site_title

############ NB get_sløyfer MÅ LEGGES INN TIL SLUTT!!!!!!###################################################
def site_refreshed ():
    til_dato = datetime.now()
    fra_dato= til_dato + relativedelta(months=-1)
    historiskData={}
    sløyfer=['heatTrace1']
    #sløyfer=get_sløyfer()
    #print(sløyfer)
    for i in sløyfer:
        historiskData[i] = update_historiskData(i)
    return historiskData, til_dato, fra_dato

historiskData, til_dato, fra_dato = site_refreshed()

layout = html.Div([
    header,
    html.Div(id='site-title-div'),

    html.Div([
    html.Label('Fra dato'),
    dcc.Input(id='fra_Dato', value=fra_dato.strftime("%Y-%m-%d %H:%M:%S"), type='text',placeholder="YYYY-MM-DD HH:MM:SS",debounce=True),

    html.Label('Til dato'),
    dcc.Input(id='til_Dato', value=til_dato.strftime("%Y-%m-%d %H:%M:%S"), type='text',placeholder="YYYY-MM-DD HH:MM:SS",debounce=True),]),
    html.Div([dcc.Dropdown(
                            id='måle-valg',
                            options=[{'label': s,'value':s} for s in målinger_dict.keys()],
                            #value='Aktiv effekt',
                            placeholder="Velg en eller flere målinger",
                            multi=True
                            )
    ]),
    html.Div([dcc.Graph(id="my-graph")]),


    # Hidden div inside the app that stores the intermediate value
    dbc.Button(id='historisk-data', style={'display': 'none'}),
    

])  

def callbacks(app):
    layout_callbacks(app)
    update_sløyfe_callback(app, [['site-title-div', get_site_title]])

    #Refresh dato og data ved refresh side
    @app.callback([Output('historisk-data', 'children'),
                    Output('til_Dato', 'value'),
                    Output('fra_Dato', 'value')],
                    [Input('historisk-data', 'n_clicks'),
                    ])

    def update_refresh(n):
        historiskData, til_dato, fra_dato = site_refreshed()
        til_dato=til_dato.strftime("%Y-%m-%d %H:%M:%S")
        fra_dato=fra_dato.strftime("%Y-%m-%d %H:%M:%S")
        return historiskData, til_dato, fra_dato

    @app.callback(
        dash.dependencies.Output('my-graph', 'figure'),
        [Input('fra_Dato', 'value'),
        Input('til_Dato', 'value'),
        Input('måle-valg', 'value'),
        Input('historisk-data', 'children')],
        [State(component_id='url', component_property='pathname'),
        ])

    def update_figure(fra_dato, til_dato, måle_valg, historiskData, url):
        trace1=[]
        trace2=[]
        trace3=[]
        trace4=[]
        trace5=[]
        trace6=[]
        trace7=[]
        trace8=[]
        trace9=[]
        trace10=[]
        trace11=[]
        ctx = dash.callback_context
        states = ctx.states
        pathname = states['url.pathname']
        sløyfe_valg = get_sløyfe_from_pathname(pathname)

        for måling in måle_valg:
            if måling == "Temperatur":
                trace1 = go.Scatter(y=historiskData[sløyfe_valg]["Temperatur-Sensor"]["temperature"],
                                    x=historiskData[sløyfe_valg]["Temperatur-Sensor"]["timeReceived"],
                                    mode='lines+markers',
                                    marker={"size": 3.5} ,
                                    name="Temperatur")
            if måling == "Aktiv effekt":
                trace2 = go.Scatter(y=historiskData[sløyfe_valg]["Power-Switch"]["activePower"],
                                    x=historiskData[sløyfe_valg]["Power-Switch"]["timeReceived"],
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Aktiv effekt")
            if måling == "Reaktiv effekt":
                trace3 = go.Scatter(y=historiskData[sløyfe_valg]["Power-Switch"]["reactivePower"],
                                    x=historiskData[sløyfe_valg]["Power-Switch"]["timeReceived"] ,
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Reaktiv effekt")
            if måling == "Tilsynelatende effekt":
                trace4 = go.Scatter(y=historiskData[sløyfe_valg]["Power-Switch"]["apparentPower"],
                                    x=historiskData[sløyfe_valg]["Power-Switch"]["timeReceived"] ,
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Tilsynelatende effekt")
            if måling == "Aktiv energi":
                trace5 = go.Scatter(y=historiskData[sløyfe_valg]["Power-Switch"]["activeEnergy"],
                                    x=historiskData[sløyfe_valg]["Power-Switch"]["timeReceived"],
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Aktiv energi")
            if måling == "Tilsynelatende energi":
                trace6 = go.Scatter(y=historiskData[sløyfe_valg]["Power-Switch"]["apparentEnergy"],
                                    x=historiskData[sløyfe_valg]["Power-Switch"]["timeReceived"], 
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Tilsynelatende energi")      
            if måling == "Reaktiv energi":
                trace7 = go.Scatter(y=historiskData[sløyfe_valg]["Power-Switch"]["reactiveEnergy"],
                                    x=historiskData[sløyfe_valg]["Power-Switch"]["timeReceived"], 
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Reaktiv energi") 
            if måling == "Spenning":
                trace8 = go.Scatter(y=historiskData[sløyfe_valg]["Power-Switch"]["voltage"],
                                    x=historiskData[sløyfe_valg]["Power-Switch"]["timeReceived"], 
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Spenning") 
            if måling == "Strøm":
                trace9 = go.Scatter(y=historiskData[sløyfe_valg]["Power-Switch"]["current"],
                                    x=historiskData[sløyfe_valg]["Power-Switch"]["timeReceived"], 
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Strøm") 
            if måling == "Frekvens":
                trace10 = go.Scatter(y=historiskData[sløyfe_valg]["Power-Switch"]["frequency"],
                                     x=historiskData[sløyfe_valg]["Power-Switch"]["timeReceived"], 
                                     mode='lines+markers',
                                     marker={"size": 3.5},
                                     name="Frekvens") 
            if måling == "Kjøretid":
                trace11 = go.Scatter(y=historiskData[sløyfe_valg]["Power-Switch"]["runTime"],
                                    x=historiskData[sløyfe_valg]["Power-Switch"]["timeReceived"], 
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Kjøretid") 

        data = [trace1,trace2,trace3,trace4,trace5,trace6,trace7,trace8,trace9,trace10,trace11]
        return {"data": data,
                "layout": go.Layout(xaxis=dict(range=[fra_dato,til_dato]),
                                    title="Historikk",
                                    autosize=False,
                                    width=2100,
                                    height=900,
                                    margin={'l':100,'r':100,'t':50,'b':50},
                                                    )}