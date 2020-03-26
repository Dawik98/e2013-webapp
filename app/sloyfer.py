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
from opp_temp import update_tempData
from opp_meter import update_meterData

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

#Knytter sammen streng i drop-down meny og streng som brukes til å velge container i database.
sløyfer_dict={"Sløyfe 1":"heatTrace1",
              "Sløyfe 2":"heatTrace2",
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
#Defninerer hvordan siden skal se ut. Med overskrifter, menyer, grafer osv...
layout = html.Div([
    html.Label('Sløyfe valg'),
    dcc.Dropdown(
        id='sløyfe-valg',
        options=[{'label': s,'value': s} for s in sløyfer_dict.keys()],
        value='Sløyfe 1'
    ),    
    
    html.Label('Antall målinger'),
    dcc.Input(id='AntallMålinger', value='60', type='text',placeholder="Velg antall målinger",debounce=True),
    #Grad til temperatur
    dcc.Graph(id='live-graph', animate=False),
        dcc.Interval(
            id='graph-update',
            #Oppdaterer hvert 15. sekund. Gri tid til å lese fra database
            interval=15*1000,
            n_intervals = 1
    ),
    html.Label('Målerelé'),
    dcc.Dropdown(
        id='måle-valg',
        options=[{'label': s,'value': s} for s in målinger_dict.keys()],
        value='Aktiv effekt',
        #multi=True
    ),
    #Graf til målerelé
    dcc.Graph(id='live-graph2', animate=False),
        dcc.Interval(
            id='graph-update2',
            #Oppdater hvert 17. sekund, vil ikke overlappe.
            interval=17*1000,
            n_intervals = 1
    ),
])
# Callbacks kjører hele tiden, og oppdater verdier som ble definert i layout. 
def callbacks(app):
    # Live temperatur data
    @app.callback(Output('live-graph', 'figure'),
            [Input('graph-update', 'n_intervals'),
            Input('sløyfe-valg', 'value'),
            Input('AntallMålinger','value')
            ])   
    def update_graph_scatter(n,sløyfe_valg,antall_målinger):
        try:
            #henter inn ny data
            ts_UTC, temp = update_tempData(antall_målinger, sløyfer_dict[sløyfe_valg])
            #tilordner X og Y
            

            X=ts_UTC[:int(antall_målinger)]
            Y=temp[:int(antall_målinger)]
            data = plotly.graph_objs.Scatter(
                    y=Y,
                    x=X,
                    name='Scatter',
                    mode= 'lines+markers'
                    )
            return {'data': [data],'layout' : go.Layout(xaxis=dict(range=[(min(X)),(max(X))]),
                                                         yaxis=dict(range=[0,120],
                                                                    title='Temperatur [°C]'),
                                                         title='Temperatur Måling',
                                                         margin={'l':100,'r':100,'t':50,'b':50},

                                                         )}
        except Exception as e:
            with open('errors.txt','a') as f:
                f.write(str(e))
                f.write('\n')
    #Live målerelé data
    @app.callback(Output('live-graph2', 'figure'),
                [Input('graph-update2', 'n_intervals'),
                Input('sløyfe-valg', 'value'),
                Input('AntallMålinger','value'),
                Input('måle-valg', 'value')
                ])   
    def update_graph_scatter2(n,sløyfe_valg,antall_målinger,måle_valg):
        try:
            if antall_målinger == None:
                antall_målinger=0
            #sløyfe_valg=sløyfer_dict[sløyfe_valg]
            #måle_valg=målinger_dict[måle_valg]

            #Henter inn måledata basert på målevalg
            meterData = update_meterData(antall_målinger, sløyfer_dict[sløyfe_valg])
            #Henter ut tidsstempeler og gjør omtil dato
            ts=meterData["_ts"]
    
            X=pd.to_datetime(ts, unit='s')
            Y=meterData[målinger_dict[måle_valg]]

            data = plotly.graph_objs.Scatter(
                    y=Y,
                    x=X,
                    name='Scatter',
                    mode= 'lines+markers'
                    )
            return {'data': [data],'layout' : go.Layout(xaxis=dict(range=[(min(X)),(max(X))]),
                                                        yaxis=dict(range=[(min(Y)*.95),(max(Y)*1.05)],
                                                                    title=enhet_dict[måle_valg], tickangle=0,),
                                                        title='{}'.format(måle_valg),
                                                        margin={'l':100,'r':100,'t':50,'b':50},
                                                        )}
                                                        
                                                        
                                                        

        except Exception as e:
            with open('errors.txt','a') as f:
                f.write(str(e))
                f.write('\n')