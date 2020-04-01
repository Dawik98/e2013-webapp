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
import datetime
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


til_dato = pd.datetime.now()
fra_dato= til_dato + relativedelta(hours=-12)

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
"""
#Knytter sammen streng i drop-down meny og streng som brukes til å velge container i database.
sløyfer_dict={"Sløyfe 1":"heatTrace1",
              "Sløyfe 2":"heatTrace2",
}
"""
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

def get_site_title(chosen_sløyfe):
    site_title = html.Div(html.H1("Trendvindu for {}".format(chosen_sløyfe), id="site-title"), className="page-header") 
    return site_title

#Defninerer hvordan siden skal se ut. Med overskrifter, menyer, grafer osv...
layout = html.Div([
    header,
    html.Div(id='site-title-div'),

    html.Label('Fra dato'),
    dcc.Input(id='fra_Dato', value=fra_dato.strftime("%Y-%m-%d %H:%M:%S"), type='text',placeholder="YYYY-MM-DD HH:MM:SS",debounce=True),

    html.Label('Til dato'),
    dcc.Input(id='til_Dato', value='', type='text',placeholder="YYYY-MM-DD HH:MM:SS,'-' for live",debounce=True),

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
            interval=27*1000,
            n_intervals = 1
    ),
])
# Callbacks kjører hele tiden, og oppdater verdier som ble definert i layout. 
def callbacks(app):

    layout_callbacks(app)
    update_sløyfe_callback(app, [['site-title-div', get_site_title]])

    # Live temperatur data
    @app.callback(Output('live-graph', 'figure'),
            [Input('graph-update', 'n_intervals'),
            Input('fra_Dato', 'value'),
            Input('til_Dato','value')],
            [State(component_id='url', component_property='pathname'),
            ])   
    def update_graph_scatter(n,fra_dato, til_dato, url):
        try:   
            
            sløyfe_valg = pathname.split('/')[2]


            print("tull")
            print(sløyfe_valg)       
            if fra_dato == "":
                 return {'data': [], 'layout': {}}
            
           
            else:
                #henter inn ny data
                ts_UTC, temp = update_tempData(sløyfe_valg, fra_dato, til_dato)
                #tilordner X og Y
                X=ts_UTC
                Y=temp
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
                Input('site-title', 'value'),
                Input('fra_Dato', 'value'),
                Input('til_Dato','value'),
                Input('måle-valg', 'value')
                ])   
    def update_graph_scatter2(n,sløyfe_valg,fra_dato, til_dato, måle_valg):
        try:
                #sløyfe_valg=sløyfer_dict[sløyfe_valg]
                #måle_valg=målinger_dict[måle_valg]

                #Henter inn måledata basert på målevalg
                if fra_dato == "":
                     return {'data': [], 'layout': {}}
                
                else: 
                    meterData = update_meterData(sløyfer_dict[sløyfe_valg],fra_dato, til_dato)
                    #Henter ut tidsstempeler og gjør omtil dato
            
                    X=meterData["timeReceived"]
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