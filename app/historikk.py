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
from historie_data import update_historiskData




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

#Knytter sammen streng i drop-down meny og streng som brukes til å velge container i database.
sløyfer_dict={"Sløyfe 1":"heatTrace1",
              #"Sløyfe 2":"heatTrace2",
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

historiskData={}
for key, value in sløyfer_dict.items(): 
    historiskData[value] = update_historiskData(value)



layout = html.Div([
    html.Div([html.H1("Historikk")], style={"text-align": "center"}),
    html.Div([html.Label('Sløyfe valg'),
    dcc.Dropdown(
        id='sløyfe-valg',
        options=[{'label': s,'value': s} for s in sløyfer_dict.keys()],
        value='Sløyfe 1'
        )
    ]), 
    html.Div([
    html.Label('Fra dato'),
    dcc.Input(id='fra_Dato', value='2020-03-12 14:00:02', type='text',placeholder="YYYY-MM-DD HH:MM:SS",debounce=True),

    html.Label('Til dato'),
    dcc.Input(id='til_Dato', value='2020-03-26 14:00:02', type='text',placeholder="YYYY-MM-DD HH:MM:SS",debounce=True),]),
    html.Div([dcc.Dropdown(
                            id='måle-valg',
                            options=[{'label': s,'value':s} for s in målinger_dict.keys()],
                            #value='Aktiv effekt',
                            placeholder="Velg en eller flere målinger",
                            multi=True
                            )
    ]),
    html.Div([dcc.Graph(id="my-graph")]),
])

def callbacks(app):
    
    @app.callback(
        dash.dependencies.Output('my-graph', 'figure'),
        [Input('fra_Dato', 'value'),
        Input('til_Dato', 'value'),
        Input('måle-valg', 'value'),
        Input('sløyfe-valg','value')
        ])
    def update_figure(fra_dato, til_dato,måle_valg,sløyfe_valg):
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

        for måling in måle_valg:
            if måling == "Temperatur":
                trace1 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Temperatur-Sensor"]["temperature"],
                                    x=historiskData[sløyfer_dict[sløyfe_valg]]["Temperatur-Sensor"]["timeReceived"],
                                    mode='lines+markers',
                                    marker={"size": 3.5} ,
                                    name="Temperatur")
            if måling == "Aktiv effekt":
                trace2 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["activePower"],
                                    x=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["timeReceived"],
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Aktiv effekt")
            if måling == "Reaktiv effekt":
                trace3 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["reactivePower"],
                                    x=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["timeReceived"] ,
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Reaktiv effekt")
            if måling == "Tilsynelatende effekt":
                trace4 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["apparentPower"],
                                    x=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["timeReceived"] ,
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Tilsynelatende effekt")
            if måling == "Aktiv energi":
                trace5 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["activeEnergy"],
                                    x=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["timeReceived"],
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Aktiv energi")
            if måling == "Tilsynelatende energi":
                trace6 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["apparentEnergy"],
                                    x=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["timeReceived"], 
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Tilsynelatende energi")      
            if måling == "Reaktiv energi":
                trace7 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["reactiveEnergy"],
                                    x=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["timeReceived"], 
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Reaktiv energi") 
            if måling == "Spenning":
                trace8 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["voltage"],
                                    x=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["timeReceived"], 
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Spenning") 
            if måling == "Strøm":
                trace9 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["current"],
                                    x=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["timeReceived"], 
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Strøm") 
            if måling == "Frekvens":
                trace10 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["frequency"],
                                    x=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["timeReceived"], 
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Frekvens") 
            if måling == "Kjøretid":
                trace11 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["runTime"],
                                    x=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["timeReceived"], 
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