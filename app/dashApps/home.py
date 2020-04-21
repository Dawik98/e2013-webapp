import dash
import pandas as pd
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly
import random
import pytz
import plotly.graph_objs as go
import dash_daq as daq
from datetime import datetime
from collections import deque
from cosmosDB import read_from_db, connect_to_db
from opp_temp import update_tempData
import dash_bootstrap_components as dbc

from dashApps.layout import header, update_sløyfe_callback, get_sløyfe_from_pathname
from dashApps.layout import callbacks as layout_callbacks

def get_home_table():
    from dashApps.innstillinger import get_sløyfer 
    from mqttCommunication import controller
    from cosmosDB import read_from_db

    sløyfer = get_sløyfer()

    table_header = [html.Thead(html.Tr([html.Th("Sløyfe"), html.Th("Siste måling", colSpan = 2, style={'width':'270px'}), html.Th("Avvik"), html.Th("Alarm status")]))]
    table_rows = []
    
    for sløyfe in sløyfer:
        
        # Få tak i siste måling i sløyfen
        query = "SELECT TOP 1 * FROM {0} WHERE {0}.deviceType = 'tempSensor' ORDER BY {0}.timeReceived DESC".format(sløyfe)
        last_messurment = read_from_db(sløyfe, query)
        last_temp = last_messurment[0]['temperature']
        last_messure_time = last_messurment[0]['timeReceived']

        def last_temp_messerument_label(label):
            alarm_link = html.A(label, href='/trend/{}'.format(sløyfe), style={'color':'#3E3F3A'})
            return alarm_link
        
        last_temp_link = last_temp_messerument_label("{} °C".format(last_temp))
        last_messure_time_link = last_temp_messerument_label(last_messure_time)

        # Finn avviket
        try:
            setpoint = controller[sløyfe].setpoint
            if setpoint == 0:
                avvik = "Regulator er ikke aktiv"
            else:
                avvik = setpoint - last_temp
                avvik = '{}°C'.format(avvik)
        except:
            avvik = "Fant ingen regulator"

        #Finn alarm status
        query = "SELECT TOP 1 * FROM {0} WHERE {0}.deviceType = 'tempSensor' AND {0}.alarmConfirmed = false ORDER BY {0}.timeReceived DESC".format(sløyfe)
        last_unconfirmed_alarm = read_from_db(sløyfe, query)
        
        def alarm_status_label(label):
            alarm_link = html.A(label, href='/alarmer/{}'.format(sløyfe), style={'color':'#3E3F3A'})
            return alarm_link

        try:
            if last_unconfirmed_alarm[0]['timeReceived'] == last_messure_time:
                alarm_label = [html.I(className='fas fa-exclamation-circle mr-2', style={'color':'red'}), "Aktiv alarm"]
                alarm_status = alarm_status_label(alarm_label)
            else:
                alarm_label = [html.I(className='fas fa-exclamation-circle mr-2', style={'color':'#f4d53c'}), "Ukvitterte alarmer"]
                alarm_status = alarm_status_label(alarm_label)
        except:
            alarm_label = [html.I(className='fas fa-check-circle mr-2', style={'color':'#86d01b'}), "Ingen nye alarmer"]
            alarm_status = alarm_status_label(alarm_label)
        
        row = html.Tr([html.Td(sløyfe), html.Td(last_temp_link, style={'width':'100px'}), html.Td(last_messure_time_link, style={'width':'170px'}), html.Td(avvik), html.Td(alarm_status)])

        table_rows.append(row)
        
    table_body=[html.Tbody(table_rows)]
    return dbc.Table(table_header+table_body, bordered=True)

def serve_layout():
    layout = html.Div([
        header,
        dbc.Container([

            html.H1("Sløyfe oversikt:", className="mb-2"),
            html.Div(get_home_table(), id='table', className='tableFixHead')
        ])#container
    ])
    return layout

layout = serve_layout


def callbacks(app):
    layout_callbacks(app)


    