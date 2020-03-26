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
    html.Div([dcc.Input(id='Antall-Dager', value='60', type='text')]),
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
        [Input('Antall-Dager', 'value'),
        Input('måle-valg', 'value'),
        Input('sløyfe-valg','value')
        ])
    def update_figure(selected_days,måle_valg,sløyfe_valg):
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
                                    x=pd.to_datetime(historiskData[sløyfer_dict[sløyfe_valg]]["Temperatur-Sensor"]["_ts"],unit='s'), 
                                    mode='lines+markers',
                                    marker={"size": 3.5} ,
                                    name="Temperatur")
            if måling == "Aktiv effekt":
                trace2 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["activePower"],
                                    x=pd.to_datetime(historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["_ts"],unit='s'), 
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Aktiv effekt")
            if måling == "Reaktiv effekt":
                trace3 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["reactivePower"],
                                    x=pd.to_datetime(historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["_ts"],unit='s'), 
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Aktiv effekt")
            if måling == "Tilsynelatende effekt":
                trace4 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["apparentPower"],
                                    x=pd.to_datetime(historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["_ts"],unit='s'), 
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Tilsynelatende effekt")
            if måling == "Aktiv energi":
                trace5 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["activeEnergy"],
                                    x=pd.to_datetime(historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["_ts"],unit='s'), 
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Aktiv energi")
            if måling == "Tilsynelatende energi":
                trace6 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["apparentEnergy"],
                                    x=pd.to_datetime(historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["_ts"],unit='s'), 
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Tilsynelatende energi")      
            if måling == "Reaktiv energi":
                trace7 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["reactiveEnergy"],
                                    x=pd.to_datetime(historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["_ts"],unit='s'), 
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Reaktiv energi") 
            if måling == "Spenning":
                trace8 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["voltage"],
                                    x=pd.to_datetime(historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["_ts"],unit='s'), 
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Spenning") 
            if måling == "Strøm":
                trace9 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["current"],
                                    x=pd.to_datetime(historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["_ts"],unit='s'), 
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Strøm") 
            if måling == "Frekvens":
                trace10 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["frequency"],
                                    x=pd.to_datetime(historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["_ts"],unit='s'), 
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Frekvens") 
            if måling == "Kjøretid":
                trace11 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["runTime"],
                                    x=pd.to_datetime(historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["_ts"],unit='s'), 
                                    mode='lines+markers',
                                    marker={"size": 3.5},
                                    name="Kjøretid") 

        data = [trace1,trace2,trace3,trace4,trace5,trace6,trace7,trace8,trace9,trace10,trace11]
        return {"data": data,
                "layout": go.Layout(
                                    title="Historikk",
                                    margin={'l':100,'r':100,'t':50,'b':50},
                                                    )}
        """ 
         print(målinger_dict[måling])
            if måling == "Temperatur":
                traces.append(go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Temperatur-Sensor"]["temperature"],
                                x=pd.to_datetime(historiskData[sløyfer_dict[sløyfe_valg]]["Temperatur-Sensor"]["_ts"],unit='s'), 
                                mode='lines+markers',
                                marker={"size": 3.5} ,
                                name="Temperatur"))
            elif måling != "Temperatur": 
                #print(måle_valg)
                #print(måling)
                traces.append(go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"][målinger_dict[måling]],
                                x=pd.to_datetime(historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["_ts"],unit='s'), 
                                mode='lines+markers',
                                marker={"size": 3.5},
                                name=måling))
        print(traces)

        
        """  