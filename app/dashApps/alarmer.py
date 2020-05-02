"""
alarmer.py inneholder:
    - layout og callbacks som brukes på Alarm siden
    - funksjon for å kvittere alarmer
"""

import dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_core_components as dcc 
import dash_html_components as html 
import dash_bootstrap_components as dbc

from datetime import datetime, timedelta

from cosmosDB import read_from_db, replace_in_db

#import standard layout
from dashApps.layout import header, update_sløyfe_callback, get_sløyfe_from_pathname
from dashApps.layout import callbacks as layout_callbacks

from dashApps.innstillinger import get_alarms, get_devices_eui

#num_of_alarms = '25'
#time_range = 'day'
#not_confirmed_alarms = []

def get_site_title(chosen_sløyfe):
    """
    get_site_title returner side tittel som vises helt øvers på siden og sier hvilken sløyfe som vises på siden 

    Parameters
    ----------
    chosen_sløyfe : string
        navn på sløyfen som er valgt

    Returns
    -------
    dash_html_components
        En H1 header som inneholder side tittel
    """
    site_title = html.Div(html.H1("Alarmer for {}".format(chosen_sløyfe), id="site-title"), className="page-header") 
    return site_title

site_title = html.Div(html.H1("Alarmer for alle sløyfer"), className="page-header") 

def confirm_alarms(chosen_sløyfe):
    """
    confirm_alarms kvitterer alle ukvitterte alarmer

    Parameters
    ----------
    chosen_sløyfe : string
        navn på sløyfen som er valgt
    """

    # hent alle ukvitterte alarmer
    #query = "SELECT * FROM {0} WHERE {0}.deviceType = 'tempSensor' AND {0}.alarmConfirmed = false".format(chosen_sløyfe)
    query = "SELECT * FROM {0} WHERE {0}.alarmConfirmed = false".format(chosen_sløyfe)
    unconfirmed_alarms = read_from_db(chosen_sløyfe, query)

    # gå gjennom alle alarmer og kvitter de
    for alarm_data in unconfirmed_alarms:
        id_ = alarm_data['id']
        # slett all metadata til item
        del alarm_data['_rid']
        del alarm_data['_self']
        del alarm_data['_etag']
        del alarm_data['_attachments']
        del alarm_data['_ts']

        alarm_data['alarmConfirmed'] = True
        # Prøver å kvittere alarmen helt til det er vellykke, siden noen ganger får man ikke tilgang til databasen
        # når andre deler av appen prøver å hente data fra databasen
        while True:
            try:
                replace_in_db(id_, chosen_sløyfe, alarm_data)
                break
            except:
                print("couldn't coonfirm alarm... trying again")

def get_time_range(time_interval):
    """
    get_time_range finner ut dato og tid en hvis tidsinterval tilbake i tid

    Parameters
    ----------
    time_interval : string
        'dag', 'uke', 'måned' eller 'Alle'

    Returns
    -------
    string
        dato og tid på formen: 'år-måned-dag time:minutt'
    """
    if time_interval == 'dag':
        interval = timedelta(days=1)
    elif time_interval == 'uke':
        interval = timedelta(days=7)
    elif time_interval == 'måned':
        interval = timedelta(days=31)
    else:
        return 'Alle'

    now = datetime.now()

    result = now - interval
    result = datetime.strftime(result, '%Y-%m-%d %H:%M')
    return result

def get_alarm_table(time_interval, chosen_sløyfe):
    """
    get_alarm_table lager en tabell som inneholder alle alarmer fra valgt tidsperiode

    Parameters
    ----------
    time_interval : string - 'dag', 'uke', 'måned', 'Alle'
        Definerer hvor gamle alarmer som skal lastes inn
    chosen_sløyfe : string
        navn på sløyfen som er valgt

    Returns
    -------
    dash_bootstrap_components
        dbc.Table som har alle ønskede alrmer
    """
    time_range = get_time_range(time_interval)

    #alarms = get_alarms(chosen_sløyfe)
    #min_val = alarms[0]
    #max_val = alarms[1]

    #print("updating from " + time_range)

    if (time_interval != "Alle"):
        query = "SELECT * FROM {0} WHERE {0}.timeReceived > '{1}' AND {0}.deviceType = 'tempSensor' AND {0}.alarmValue = true ORDER BY {0}.timeReceived DESC".format(chosen_sløyfe, time_range)
        abnormal_values = read_from_db(chosen_sløyfe, query)
    else:
        query = "SELECT * FROM {0} WHERE {0}.deviceType = 'tempSensor' AND {0}.alarmValue = true ORDER BY {0}.timeReceived DESC".format(chosen_sløyfe)
        abnormal_values = read_from_db(chosen_sløyfe, query)

    table_header = [html.Thead(html.Tr([html.Th("Tid"), html.Th("Enhetens plassering"), html.Th("Enhetens Eui"), html.Th("Verdi"),]))]
    table_rows = []
    
    for item in abnormal_values:
        # Gjør dato formatet for at den skal bli mer lesbar
        time = datetime.strptime(item["timeReceived"], '%Y-%m-%d %H:%M:%S')
        time = datetime.strftime(time, '%d.%m.%Y   %H:%M')
        devicePlacement = item["devicePlacement"]
        deviceEui = item["deviceEui"]
        temperature = item["temperature"]

        # Lag ny rad for hver alarm
        # Hvis alarmen ikke er kvittert bruk rød bakgrunnsfarge
        if item['alarmConfirmed'] == False:
            row = html.Tr([html.Td(time), html.Td(devicePlacement), html.Td(deviceEui), html.Td("{} °C".format(temperature), className="scrollBarColl")], className='table-danger')
        else:
            row = html.Tr([html.Td(time), html.Td(devicePlacement), html.Td(deviceEui), html.Td("{} °C".format(temperature), className="scrollBarColl")])

        table_rows.append(row)

    table_body=[html.Tbody(table_rows)]

    return dbc.Table(table_header+table_body, bordered=True)

def comm_alarms(chosen_sløyfe):
    from mqttCommunication import gatewayFile
    label = []

    # Sjekker gateway status
    f = open(gatewayFile, 'r')
    lines = f.read().splitlines()
    status = lines[-1]
    status_time = status[status.find("[")+1:status.find("]")]

    if 'Lost connection' in status:
        label.append(html.Li('Mistet kontakt med gateway {}\n'.format(status_time), className='spaced-list'))

    #Sjekker status til enhetene
    for device_eui in get_devices_eui(chosen_sløyfe):
        try:
            query = "SELECT TOP 1 * FROM {0} WHERE {0}.deviceEui = '{1}' ORDER BY {0}.timeReceived DESC".format(chosen_sløyfe, device_eui)
            data = read_from_db(chosen_sløyfe, query)
            data = data[0]
        except:
            label.append(html.Li("Finnes ingen data mottatt fra {}\n".format(device_eui), className='spaced-list'))
            continue

        # Finner ut hvor lenge siden data ble sendt
        message_time = data['timeReceived']
        message_time = datetime.strptime(message_time, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        time_diff = now-message_time 

        if time_diff > timedelta(minutes=30):
            label.append(html.Li("Ingen data mottat fra {} siden {}\n".format(device_eui, message_time), className='spaced-list'))

    if label == []:
        label = 'Ingen problemer med kommunikasjon'
    else:
        label = html.Ul(label)

    return label

def jordfeil_alarms(chosen_sløyfe):
    label = ""

    try:
        query = "SELECT TOP 1 * FROM {0} WHERE {0}.messageType = 'ioData' AND {0}.input = true AND {0}.alarmConfirmed = false ORDER BY {0}.timeReceived DESC".format(chosen_sløyfe)
        data = read_from_db(chosen_sløyfe, query)
        data = data[0]
    except:
        return "Ingen nye jordfeil detektert"

    message_time = data['timeReceived']
    message_time = datetime.strptime(message_time, '%Y-%m-%d %H:%M:%S')

    return "Jordfeil detektert {}".format(message_time)

    
def dropdown():
    # Lag dropdown meny for å velge hvor gamle alarmer som skal lastes inn
    dropdown = dbc.DropdownMenu(label = 'dag', id='dropdown-alarms', children=[
        dbc.DropdownMenuItem('dag', id='day'),
        dbc.DropdownMenuItem('uke', id='week'),
        dbc.DropdownMenuItem('måned', id='month'),
        dbc.DropdownMenuItem('Alle', id='Alle'),
    ])

    label_dropdown = html.Div("Alarmer fra siste:", className='label-dropdown')

    return [label_dropdown, dropdown]

# Lag en knapp for kvittering av alarmer
confirm_button = dbc.Button("Kvitter alle alarmer", id='button-confirm', color="success", className='ml-5')

# layout definnneres i en funksjon for at den skal bli oppdatert når nettsiden refreshes
def serve_layout():
    layout = html.Div([
        dcc.Interval(id='refresh', n_intervals=0, interval=60*1000),
        header,
        dbc.Container([
            dbc.Row(dbc.Col(html.Div(id='site-title'))),
            dbc.Row(dropdown() + [confirm_button], className='mb-3 mt-2'),
            dbc.Row([
            dbc.Col([
                dbc.Row(html.H2("Temperaturavvik")),
                dbc.Row(html.Div(id='table', className='tableFixHead')),
            ]),

            dbc.Col([
                dbc.Row(html.H2("Kommunikasjons alarmer")),
                dbc.Row(html.Div(id='comm-alarms', style={'font-size':'medium'})),

                dbc.Row(html.H2("Jordfeil", className="mt-5")),
                dbc.Row(html.Div(id='jordfeil-alarms', style={'font-size':'medium'})),
            ], width = 5) #Col andre alarmer
            ])

        ], id='main-container', style={'max-width':'75%'}),# Container
        ])# Div
    return layout

layout = serve_layout


def callbacks(app):
    layout_callbacks(app)

    # oppdater site-title når ny sløyfe blir valgt
    update_sløyfe_callback(app, [['site-title', get_site_title],
                                 ])
    # Oppdater alarm tabellen etter en hvis tidsintervall, når alarmer kvitteres og når ny tidsintervall velges
    @app.callback(
        Output(component_id='table', component_property='children'),
        [Input(component_id='refresh', component_property='n_intervals'),
        Input(component_id='dropdown-alarms', component_property='label'),
        Input(component_id='button-confirm', component_property='n_clicks')],
        [State(component_id='url', component_property='pathname')])
    def display_layout(n_intervals, time_range, click_button, pathname):
        ctx = dash.callback_context
        triggered = ctx.triggered[0]['prop_id'].split('.')[0]

        chosen_sløyfe = get_sløyfe_from_pathname(pathname)

        if triggered == None or ctx.triggered[0]['value'] == None:
            raise PreventUpdate
            #return [get_alarm_table(time_range, chosen_sløyfe)]
        elif triggered == 'button-confirm':
            print('confirming_alarms')
            confirm_alarms(chosen_sløyfe)
            return [get_alarm_table(time_range, chosen_sløyfe)]
        else:
            chosen_sløyfe = get_sløyfe_from_pathname(pathname)
            return [get_alarm_table(time_range, chosen_sløyfe)]

    # Oppdater kommunikasjons alarmer
    @app.callback(
        Output('comm-alarms', 'children'),
        [Input('refresh', 'n_intervals')],
        [State('url', 'pathname')])
    def updtae_comm_alarms(n_intervals, pathname):
        chosen_sløyfe = get_sløyfe_from_pathname(pathname)
        return comm_alarms(chosen_sløyfe)

    @app.callback(
        Output('jordfeil-alarms', 'children'),
        [Input('refresh', 'n_intervals'),
        Input('button-confirm', 'n_clicks')],
        [State('url', 'pathname')])
    def updtae_comm_alarms(n_intervals, confirm_click, pathname):
        ctx = dash.callback_context
        triggered = ctx.triggered[0]['prop_id'].split('.')[0]
        chosen_sløyfe = get_sløyfe_from_pathname(pathname)

        if triggered == None or ctx.triggered[0]['value'] == None:
            raise PreventUpdate
            #return [get_alarm_table(time_range, chosen_sløyfe)]
        elif triggered == 'button-confirm':
            return "Ingen nye jordfeil detektert"

        else:
            return jordfeil_alarms(chosen_sløyfe)
    

    # oppdater label til dropdown menu
    @app.callback(
        Output(component_id='dropdown-alarms', component_property='label'),
        [Input(component_id='day', component_property='n_clicks'),
        Input(component_id='week', component_property='n_clicks'),
        Input(component_id='month', component_property='n_clicks'),
        Input(component_id='Alle', component_property='n_clicks'),
        ])
    def update_label(n_day, n_week, n_month, n_Alle):
        id_lookup = {'day':'dag', 'week':'uke', 'month':'måned', 'Alle':'Alle'}

        ctx = dash.callback_context

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        label_clicked = id_lookup[button_id]


        if (n_day is None and n_week is None and n_month is None and n_Alle is None) or not ctx.triggered:
            return 'dag'

        return label_clicked

