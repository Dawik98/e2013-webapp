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
                            value='Temperatur',
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
        #Henter inn data
        #historiskData=update_historiskData(sløyfe_valg)
        #Plotter temperatur
        #print(måle_valg)
        #if måle_valg == "Temperatur":
        traces=[]
        for måling in måle_valg:
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
        """                    
        trace1 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Temperatur-Sensor"]["temperature"],
                            x=pd.to_datetime(historiskData[sløyfer_dict[sløyfe_valg]]["Temperatur-Sensor"]["_ts"],unit='s'), 
                            mode='lines+markers',
                            marker={"size": 3.5} ,
                            name="Temperatur")
        trace2 = go.Scatter(y=historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["activePower"],
                            x=pd.to_datetime(historiskData[sløyfer_dict[sløyfe_valg]]["Power-Switch"]["_ts"],unit='s'), 
                            mode='lines+markers',
                            marker={"size": 3.5},
                            name="Aktiv effekt")
        """                    

        data = [traces]
        return {"data": data,
                "layout": go.Layout(
                                    title="Historikk",
                                    margin={'l':100,'r':100,'t':50,'b':50},
                                                    )}
                                                                    