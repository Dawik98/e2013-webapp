# HOME PAGE

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

from dashApps.innstillinger import get_alarms

#num_of_alarms = '25'
#time_range = 'day'
not_confirmed_alarms = []

def get_site_title(chosen_sløyfe):
    site_title = html.Div(html.H1("Alarmer for {}".format(chosen_sløyfe), id="site-title"), className="page-header") 
    return site_title

site_title = html.Div(html.H1("Alarmer for alle sløyfer"), className="page-header") 
# TODO legg til mulighet til å velge sløyfe

def get_time_range(time_interval):
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


def confirm_alarms(chosen_sløyfe):
    query = "SELECT * FROM {0} WHERE {0}.deviceType = 'tempSensor' AND {0}.alarmValue = true".format(chosen_sløyfe)
    unconfirmed_alarms = read_from_db(chosen_sløyfe, query)

    for alarm_data in unconfirmed_alarms:
        id_ = alarm_data['id']
        del alarm_data['_rid']
        del alarm_data['_self']
        del alarm_data['_etag']
        del alarm_data['_attachments']
        del alarm_data['_ts']

        alarm_data['alarmConfirmed'] = True
        replace_in_db(id_, chosen_sløyfe, alarm_data)


def get_alarm_table(time_interval, chosen_sløyfe):
    time_range = get_time_range(time_interval)

    alarms = get_alarms(chosen_sløyfe)
    min_val = alarms[0]
    max_val = alarms[1]

    print("updateing frrom " + time_range)

    if (time_interval != "Alle"):
        #get data where temp is <10 or >30
        #query = "SELECT * FROM {0} WHERE {0}.timeReceived > '{1}' AND {0}.deviceType = 'tempSensor' AND ({0}.temperature < {2} OR {0}.temperature > {3} ) ORDER BY {0}.timeReceived DESC".format(chosen_sløyfe, time_range, min_val, max_val)
        query = "SELECT * FROM {0} WHERE {0}.timeReceived > '{1}' AND {0}.deviceType = 'tempSensor' AND {0}.alarmValue = true ORDER BY {0}.timeReceived DESC".format(chosen_sløyfe, time_range, min_val, max_val)
        abnormal_values = read_from_db(chosen_sløyfe, query)
    else:
        #query = "SELECT * FROM {0} WHERE {0}.deviceType = 'tempSensor' AND ({0}.temperature < {1} OR {0}.temperature > {2} ) ORDER BY {0}.timeReceived DESC".format(chosen_sløyfe, min_val, max_val)
        query = "SELECT * FROM {0} WHERE {0}.deviceType = 'tempSensor' AND {0}.alarmValue = true ORDER BY {0}.timeReceived DESC".format(chosen_sløyfe, time_range, min_val, max_val)
        abnormal_values = read_from_db(chosen_sløyfe, query)

    table_header = [html.Thead(html.Tr([html.Th("Tid"), html.Th("Enhetens plassering"), html.Th("Enhetens Eui"), html.Th("Verdi"),]))]
    table_rows = []
    
    for item in abnormal_values:
        time = datetime.strptime(item["timeReceived"], '%Y-%m-%d %H:%M:%S')
        time = datetime.strftime(time, '%d.%m.%Y   %H:%M')
        devicePlacement = item["devicePlacement"]
        deviceEui = item["deviceEui"]
        temperature = item["temperature"]

        global not_confirmed_alarms
        not_confirmed_alarms = []
        if item['alarmConfirmed'] == False:
            not_confirmed_alarms.append(item['_self'])
            row = html.Tr([html.Td(time), html.Td(devicePlacement), html.Td(deviceEui), html.Td("{} °C".format(temperature), className="scrollBarColl")], className='table-danger')
        else:
            row = html.Tr([html.Td(time), html.Td(devicePlacement), html.Td(deviceEui), html.Td("{} °C".format(temperature), className="scrollBarColl")])

        table_rows.append(row)
        
    table_body=[html.Tbody(table_rows)]
    return dbc.Table(table_header+table_body, bordered=True)
    
dropdown = dbc.DropdownMenu(label = 'dag', id='dropdown-alarms', children=[
    dbc.DropdownMenuItem('dag', id='day'),
    dbc.DropdownMenuItem('uke', id='week'),
    dbc.DropdownMenuItem('måned', id='month'),
    dbc.DropdownMenuItem('Alle', id='Alle'),
])

label_dropdown = html.Div("Alarmer fra siste:", className='label-dropdown')

confirm_button = dbc.Button("Kvitter alarmer", id='button-confirm', color="success", className='ml-4')

layout = html.Div([
    dcc.Interval(id='refresh', n_intervals=0, interval=20*1000),
    header,
    dbc.Container([
        dbc.Row(dbc.Col(html.Div(id='site-title'))),
        dbc.Row(html.Div(id='table', className='tableFixHead')),
        dbc.Row([dbc.Col(label_dropdown, width='auto'), dbc.Col(dropdown), dbc.Col(confirm_button)], justify='start', no_gutters=True),

    ]),# Container
    ])# Div


def callbacks(app):
    layout_callbacks(app)
    update_sløyfe_callback(app, [['site-title', get_site_title],
                                 ])

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
            return [get_alarm_table(time_range, chosen_sløyfe)]
        elif triggered == 'button-confirm':
            confirm_alarms(chosen_sløyfe)
            return [get_alarm_table(time_range, chosen_sløyfe)]
        else:
            chosen_sløyfe = get_sløyfe_from_pathname(pathname)
            return [get_alarm_table(time_range, chosen_sløyfe)]

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

