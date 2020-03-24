# Instillinger

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc 
import dash_html_components as html 
import dash_bootstrap_components as dbc

import json

#import standard layout
from dashApps.layout import header
from dashApps.layout import callbacks as layout_callbacks


def print_settings():
    with open('app/settings.txt') as json_file:
        data = json.load(json_file)
        print(json.dumps(data, indent=4))

def get_settings():
    with open('app/settings.txt') as json_file:
        data = json.load(json_file)
        return data

def get_sløyfer():
    sløyfer = []
    with open('app/settings.txt') as json_file:
        data = json.load(json_file)
        for key, value in data.items():
            sløyfer.append(key)

    return sløyfer

def add_device(sløyfe, device_eui, device_type):
    device_data = {'device_eui':device_eui, 'deviceType': device_type}
    with open('app/settings.txt', 'r+') as settings_file:
        settings = json.load(settings_file)
        settings[sløyfe]['devices'].append(device_data)
        settings_file.seek(0)
        json.dump(settings, settings_file)

def remove_device(sløyfe, device_eui):
    with open('app/settings.txt', 'r+') as settings_file:
        settings = json.load(settings_file)
        n = 0
        for i in settings[sløyfe]['devices']:
            if i['device_eui'] == device_eui:
                del settings[sløyfe]['devices'][n]
            n+=1
        settings_file.seek(0)
        settings_file.truncate(0) #clear file
        json.dump(settings, settings_file)

def add_sløyfe(sløyfe):
    data = {sløyfe : 
                {'devices' : [],
                'alarm_values' : []}
            }
    with open('app/settings.txt', 'r+') as settings_file:
        settings = json.load(settings_file)
        settings.update(data)
        settings_file.seek(0)
        json.dump(settings, settings_file)

def remove_sløyfe(sløyfe):
    with open('app/settings.txt', 'r+') as settings_file:
        settings = json.load(settings_file)
        #del settings[sløyfe]
        settings.pop(sløyfe, None)
        settings_file.seek(0)
        settings_file.truncate(0) #clear file
        json.dump(settings, settings_file)

def change_alarm_values(sløyfe, alarm_values):
    with open('app/settings.txt', 'r+') as settings_file:
        settings = json.load(settings_file)
        settings[sløyfe]['alarm_values'] = alarm_values
        settings_file.seek(0)
        json.dump(settings, settings_file)

# Site components:

valgt_sløyfe = get_sløyfer()[0]

site_title = html.Div(html.H1("Instillinger for {}".format(valgt_sløyfe)), className="page-header") 

def choose_sløyfe_dropdown():
    sløyfer = get_sløyfer() 
    items = []
    for sløyfe in sløyfer:
        items.append(dbc.DropdownMenuItem(sløyfe, id=sløyfe))

    dropdown = dbc.DropdownMenu(label = "Velg sløyfe   ", id='dropdown-sløyfer', children=items)
    return dropdown

def get_settings_table(add_new = False):

    settings = get_settings()
    settings = settings[valgt_sløyfe]['devices']

    table_header = [html.Thead(html.Tr([html.Th("Enhetens eui"), html.Th("Enhet type ??")]))]
    table_rows = []


    add_eui = dbc.Input(placeholder="Skriv inn enhetens eui", type='text', id="add-eui")
    device_types = [dbc.DropdownMenuItem("Temperatur sensor", id='tempSensor'),
                    dbc.DropdownMenuItem("Power switch", id='powerSwitch')]
    add_type = dbc.DropdownMenu(device_types, label="Velg enhet type", toggleClassName="btn-outline-secondary")
    add_device_row = html.Tr([html.Td(add_eui), html.Td(add_type)])

    
    for item in settings:
        deviceEui = item["device_eui"]
        deviceType = item["deviceType"]

        row = html.Tr([html.Td(deviceEui), html.Td(deviceType),])
        table_rows.append(row)
    
    if add_new:
        table_rows.append(add_device_row)

    table_body=[html.Tbody(table_rows)]
    return dbc.Table(table_header+table_body, bordered=True)

def add_device_button():
    button = dbc.Button("Legg til ny enhet", id="add-device-button")
    return button

layout = html.Div([
    header,
    dbc.Container([
        dbc.Row([dbc.Col(site_title), dbc.Col(choose_sløyfe_dropdown())]),
        dbc.Row(html.Div(id='table', className='tableFixHead', children = [get_settings_table()])),
        dbc.Row(add_device_button())

    ]),# Container
    ])# Div


def callbacks(app):
    layout_callbacks(app)

    @app.callback(
        Output(component_id='table', component_property='children'),
        [Input(component_id='add-device-button', component_property='n_clicks'),
        ])
    def display_table(n_clicks):
        ctx = dash.callback_context

        if (n_clicks is None) or not ctx.triggered:
        # if neither button has been clicked, return "Not selected"
            return [get_settings_table()]

        settings_table = get_settings_table(add_new=True)
       

        return [settings_table]

        
#if __name__ == "__main__":
#    app.run_server(debug=True)