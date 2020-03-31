# Instillinger

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc 
import dash_html_components as html 
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

import json
import re
from itertools import zip_longest

#import standard layout
from dashApps.layout import header, update_sløyfe_callback, get_sløyfe_from_pathname
from dashApps.layout import callbacks as layout_callbacks


def print_settings():
    with open('app/settings.txt') as json_file:
        data = json.load(json_file)
        print(json.dumps(data, indent=4))

def get_settings():
    with open('app/settings.txt') as json_file:
        data = json.load(json_file)
        return data

# kopiert til layout.py
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

def change_alarm_values(sløyfe, min_value, max_value):
    alarm_values = {'min_val':min_value, 'max_val': max_value}
    with open('app/settings.txt', 'r+') as settings_file:
        settings = json.load(settings_file)
        settings[sløyfe]['alarm_values'] = alarm_values
        settings_file.seek(0)
        json.dump(settings, settings_file)

def get_alarms(sløyfe):
    alarms = []
    with open('app/settings.txt') as json_file:
        data = json.load(json_file)
        for key, value in data[sløyfe]['alarm_values'].items():
            alarms.append(value)
        print(alarms)
    return alarms

#---------------------------------------------------- Site components --------------------------------------------------------------------

# alle mulige rader må være definert på forhånd pga hvordan dash callbacks fungerer
def make_id_dict():
    remove_buttons_ids = {}
    remove_buttons = {}

    for i in range(20):
        id_ = "delete-row-{}".format(i+1)
        remove_buttons_ids[id_] = None
        remove_buttons[id_] = html.I(className="fas fa-window-close fa-pull-right fa-lg", id=id_)
    
    return remove_buttons_ids, remove_buttons
    
remove_buttons_ids, remove_buttons = make_id_dict()


def get_site_title(chosen_sløyfe):
    site_title = html.Div(html.H1("Innstillinger for {}".format(chosen_sløyfe), id="site-title"), className="page-header") 
    return site_title


def get_settings_table(chosen_sløyfe):

    print('chosens sløyfe = '+chosen_sløyfe)
    settings = get_settings()
    settings = settings[chosen_sløyfe]['devices']
    print(settings)

    table_header = [html.Thead(html.Tr([html.Th("Enhetens eui"), html.Th("Enhet")]))]
    table_rows = []

    add_eui = dbc.Input(placeholder="Skriv inn enhetens eui", type='text', id="add-eui")
    device_types = [dbc.DropdownMenuItem("Temperatur sensor", id='tempSensor'),
                    dbc.DropdownMenuItem("Power switch", id='powerSwitch')]
    add_type = dbc.DropdownMenu(device_types, label="Velg enhet type", id="add-type")#, toggleClassName="btn-outline-secondary")
    add_device_row = dbc.Collapse(html.Tr([html.Td(add_eui), html.Td(add_type)]), id='add-row-collapse')#, is_open=False)

    # lag alle mulige rader i tabellen, hvis bare de som har tilskrevet enhet
    for (key, status), setting_item in zip_longest(remove_buttons_ids.items(), settings):

        if setting_item:
            deviceEui = setting_item["device_eui"]
            deviceType = setting_item["deviceType"]

            if deviceType == "tempSensor":
                deviceType = "Temperatur sensor"
            elif deviceType == "powerSwitch":
                deviceType = "Power switch"

            delete_button = remove_buttons[key]
            remove_buttons_ids[key]=deviceEui

            row = html.Tr([html.Td(deviceEui), html.Td([deviceType, delete_button]),])
            table_rows.append(row)
        elif setting_item == None:
            deviceEui = ""
            deviceType = ""

            delete_button = remove_buttons[key]

            row = html.Tr([html.Td(deviceEui), html.Td([deviceType, delete_button]),], style={'display':'none'})
            table_rows.append(row)

    table_rows.append(add_device_row)

    table_body=[html.Tbody(table_rows)]
    return dbc.Table(table_header+table_body, bordered=True)

def add_device_button():
    button = dbc.Button("Legg til ny enhet", id="add-device-button")
    button_collapse = dbc.Collapse(button, id='add-device-button-collapse', is_open=True, className="collapsing-no-slide-animation")
    return button_collapse

def confirm_buttons():
    button_confirm = dbc.Button("Legg til", id="confirm-add-device-button", color='success', className='mr-2')
    button_cancel = dbc.Button("Avbryt", id="cancel-add-device-button", color='danger', className='mr-2')
    button_collapse = dbc.Collapse(html.Div([button_confirm, button_cancel]), id='confirm-add-device-button-collapse', is_open=False, className="collapsing-no-slide-animation")
    return button_collapse

def controller_settings():
    controller_settings = html.Div([
    dbc.Row([html.H2("Regulator-innstillinger"), html.P(id='dummy')]),
    dbc.Row([dbc.Col(html.P("Setpunkt:", id="test-label"), width=3), dbc.Col(dbc.Input(type='number', step=0.1, id="setpoint-input"), width=4)], justify='start'),
    dbc.Row([dbc.Button("Oppdater regulator innstillinger", color='success', id='update-controller-button')])
    ])
    return controller_settings

def get_alarm_settings():
    curr_alarm_val = get_alarms('heatTrace1')
    print("curr_alarms={}".format(curr_alarm_val))
    alarm_settings = html.Div(id='alarm-settings', children =[
        dbc.Row([html.H2("Alarm innstillinger")], className='mt-5'),
        dbc.Row([
            dbc.Col(html.P("Max. temperatur: [°C]"), width=4),
            dbc.Col(dbc.Input(type='number', step=1, id='max-temp-input', value=curr_alarm_val[1]), width=2)
        ]),
        dbc.Row([
            dbc.Col(html.P("Min. temperatur: [°C]"), width=4),
            dbc.Col(dbc.Input(type='number', step=1, id='min-temp-input', value=curr_alarm_val[0]), width=2)
        ]),
        dbc.Row(
            [dbc.Collapse(id='collapse-alarm-confirm', is_open=False, children = dbc.Button("Oppdater alarm innstillinger", id='button-alarm-confirm'))
        ])

    ])
    return alarm_settings

layout = html.Div([
    header,
    dbc.Container([
        dbc.Row([dbc.Col(html.Div(id='site-title-div'))]),
        dbc.Row([
            dbc.Col([
                dbc.Row(html.Div(html.Div(id='table-div'), id='table', className='tableFixHead')),
                dbc.Row([add_device_button()]),
                dbc.Row([confirm_buttons()])
            ]),
            dbc.Col([    
                controller_settings(),
                get_alarm_settings()
                ])
            ])
    ]),# Container
    ])# Div


def callbacks(app):
    layout_callbacks(app)

    update_sløyfe_callback(app, [['site-title-div', get_site_title],
                                 ['table-div', get_settings_table]])

    # Vis / skjul tabellraden for å leggen inn ny enhet
    @app.callback(
        Output(component_id='add-row-collapse', component_property='is_open'),
        [Input(component_id='add-device-button', component_property='n_clicks'),
        Input(component_id='confirm-add-device-button', component_property='n_clicks'),
        Input(component_id='cancel-add-device-button', component_property='n_clicks'),],
        [State(component_id='add-row-collapse', component_property='is_open'),
        ])
    def display_add_row(click_add_device, click_confirm_add, click_cancel_add, is_open):
        if click_add_device or click_cancel_add or click_confirm_add:
            return not is_open
        return False

    # Vis / skjul knapp for å legge til ny enhet
    @app.callback(
        Output(component_id='add-device-button-collapse', component_property='is_open'),
        [Input(component_id='add-device-button', component_property='n_clicks'),
        Input(component_id='confirm-add-device-button', component_property='n_clicks'),
        Input(component_id='cancel-add-device-button', component_property='n_clicks'),],
        [State(component_id='add-device-button-collapse', component_property='is_open'),
        State(component_id='confirm-add-device-button-collapse', component_property='is_open'),
        ])
    def display_add_buttons(click_add_device, click_confirm_add, click_cancel_add, is_add_button_open, is_confirm_bottons_open):
        if click_add_device or click_confirm_add or click_cancel_add:
            if is_add_button_open:
                return False
            if is_confirm_bottons_open:
                return True
        else:
            return True

    # Vis / skjul knapper for godkjenning / ikke godkjening for å legge til ny enhet
    @app.callback(
        Output(component_id='confirm-add-device-button-collapse', component_property='is_open'),
        [Input(component_id='add-device-button', component_property='n_clicks'),
        Input(component_id='confirm-add-device-button', component_property='n_clicks'),
        Input(component_id='cancel-add-device-button', component_property='n_clicks'),],
        [State(component_id='add-device-button-collapse', component_property='is_open'),
        State(component_id='confirm-add-device-button-collapse', component_property='is_open'),
        ])
    def display_confirm_buttons(click_add_device, click_confirm_add, click_cancel_add, is_add_button_open, is_confirm_bottons_open):
        if click_add_device or click_confirm_add or click_cancel_add:
            if is_add_button_open:
                return True
            if is_confirm_bottons_open:
                return False
        else:
            return False

    # Reset input og sensor type valg ved å trykke avbryt knappen og legg til knappen
    @app.callback(
        Output(component_id='add-eui', component_property='value'),
        [Input(component_id='cancel-add-device-button', component_property='n_clicks'),
        Input(component_id='confirm-add-device-button', component_property='n_clicks'),
        ])
    def display_confirm_buttons(click_cancel_add, click_confirm_add):
        if click_cancel_add or click_confirm_add:
            return ""

    # Oppdater dropmenu label når en enhet type velges eller avbryt knappen eller legg til knappen trykkes
    @app.callback(
        Output(component_id='add-type', component_property='label'),
        [Input(component_id='tempSensor', component_property='n_clicks'),
        Input(component_id='powerSwitch', component_property='n_clicks'),
        Input(component_id='cancel-add-device-button', component_property='n_clicks'),
        Input(component_id='confirm-add-device-button', component_property='n_clicks'),
        ])
    def display_confirm_buttons(click_tempSensor, click_powerSwitch, click_cancel_add, click_confirm_add):
        id_lookup = {'tempSensor':'Temperatur sensor', 'powerSwitch':'Power Switch', 'cancel-add-device-button':'Velg enhet type', 'confirm-add-device-button':'Velg enhet type'}

        try:
            ctx = dash.callback_context

            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            label_clicked = id_lookup[button_id]

            if (click_tempSensor is None and click_powerSwitch is None) or not ctx.triggered:
            # if neither button has been clicked, return "Not selected"
                return "Velg enhet type"

            return label_clicked
        except:
            return "Velg enhet type"
        

    def delete_buttons_inputs():
        inputs = []

        for key, status in remove_buttons_ids.items():
            inputs.append(Input(component_id=key, component_property='n_clicks'))

        #print(inputs)

        return inputs

    # Oppdater tabellen
    @app.callback(
        Output(component_id='table', component_property='children'),
        [Input(component_id='confirm-add-device-button', component_property='n_clicks')]+delete_buttons_inputs(),
        [State(component_id='add-eui', component_property='value'),
        State(component_id='add-type', component_property='label'),
        State(component_id='url', component_property='pathname'),
        ])
    def update_settings(click_confirm_add, *args, **kwargs):

        ctx = dash.callback_context
        states = ctx.states
        inputs = ctx.inputs

        pathname = states['url.pathname']
        chosen_sløyfe = get_sløyfe_from_pathname(pathname)

        triggered_button = ctx.triggered[0]['prop_id'].split('.')[0]
        print(ctx.triggered)
        print('triggered by "{}" '.format(triggered_button))

        device_eui = states['add-eui.value']
        device_type = states['add-type.label']

        if triggered_button == None or ctx.triggered[0]['value'] == None:
            return get_settings_table(chosen_sløyfe)
        elif triggered_button == 'confirm-add-device-button':
            add_device(chosen_sløyfe, device_eui, device_type)
            return get_settings_table(chosen_sløyfe)
        elif triggered_button != 'confirm-add-device-button':
            eui = remove_buttons_ids[triggered_button]
            print(eui)
            remove_device(chosen_sløyfe, eui)
            return get_settings_table(chosen_sløyfe)

        print("states")
        print(ctx.states)
        print("inputs")
        print(ctx.inputs)

        print("Args:")
        print(args)


    # dummy update
    @app.callback(
        Output('dummy', 'children'),
        [Input('update-controller-button', 'n_clicks')],
        [State('setpoint-input', 'value')]
    )
    def update_test_label(button_click, setpoint_value):
        print(setpoint_value)
        
        return ""

    @app.callback(
        Output(component_id='collapse-alarm-confirm', component_property='is_open'),
        [Input(component_id='max-temp-input', component_property='value'),
        Input(component_id='min-temp-input', component_property='value')
        ])
    def show_confirm_alarm_settings(max_temp, min_temp):
        #TODO bytte 'heatTrace1' her !!!!!!!!!
        curr_alarm_val = get_alarms('heatTrace1')
        # hvis oppdater knappen bare når veriden er forandret
        if [min_temp, max_temp] == curr_alarm_val:
            return False
        else:
            print ("max = {}; min = {}".format(max_temp, min_temp))
            return True

    @app.callback(
        Output(component_id='alarm-settings', component_property='children'),
        [Input(component_id='button-alarm-confirm', component_property='n_clicks'),
        ],
        [State(component_id='min-temp-input', component_property='value'),
        State(component_id='max-temp-input', component_property='value'),
        ])
    def update_alarms(button_click, min_temp, max_temp):

        ctx = dash.callback_context
        triggered_button = ctx.triggered[0]['prop_id'].split('.')[0]
        print('triggered by "{}" '.format(triggered_button))

        if triggered_button == None or ctx.triggered[0]['value'] == None:
            raise PreventUpdate
        elif triggered_button == 'button-alarm-confirm':
            change_alarm_values('heatTrace1', min_temp, max_temp)
            return get_alarm_settings()
        else:
            return get_alarm_settings()