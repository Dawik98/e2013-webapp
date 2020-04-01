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
from mqttCommunication import claimMeterdata, activateHeatTrace, deactivateHeatTrace, controller1, get_output_state

# Importer standard layout
from dashApps.layout import header, update_sløyfe_callback, get_sløyfe_from_pathname
from dashApps.layout import callbacks as layout_callbacks

# GLOBALE VARIABLER
prew_setpoint_confirm_count = 0
prew_Kp_confirm_count = 0
prew_Ti_confirm_count = 0
prew_dutycycle_confirm_count = 0
prew_manual_actuation_confirm_count = 0

# Velges avhengig av om appen kjøres lokalt eller i Azure
# settingsFile = 'settings.txt' # Azure
settingsFile = 'app/settings.txt' # Lokalt

def print_settings():
    with open(settingsFile) as json_file:
        data = json.load(json_file)
        print(json.dumps(data, indent=4))

def get_settings():
    with open(settingsFile) as json_file:
        data = json.load(json_file)
        return data

def get_sløyfer():
    sløyfer = []
    with open(settingsFile) as json_file:
        data = json.load(json_file)
        for key, value in data.items():
            sløyfer.append(key)
    return sløyfer

def add_device(sløyfe, device_eui, device_type):
    device_data = {'device_eui':device_eui, 'deviceType': device_type}
    with open(settingsFile, 'r+') as settings_file:
        settings = json.load(settings_file)
        settings[sløyfe]['devices'].append(device_data)
        settings_file.seek(0)
        json.dump(settings, settings_file)

def remove_device(sløyfe, device_eui):
    with open(settingsFile, 'r+') as settings_file:
        settings = json.load(settings_file)
def print_settings():
    with open(settingsFile) as json_file:
        data = json.load(json_file)
        print(json.dumps(data, indent=4))

def get_settings():
    with open(settingsFile) as json_file:
        data = json.load(json_file)
        return data

# kopiert til layout.py
def get_sløyfer():
    sløyfer = []
    with open(settingsFile) as json_file:
        data = json.load(json_file)
        for key, value in data.items():
            sløyfer.append(key)

    return sløyfer

def add_device(sløyfe, device_eui, device_type):
    device_data = {'device_eui':device_eui, 'deviceType': device_type}
    with open(settingsFile, 'r+') as settings_file:
        settings = json.load(settings_file)
        settings[sløyfe]['devices'].append(device_data)
        settings_file.seek(0)
        json.dump(settings, settings_file)

def remove_device(sløyfe, device_eui):
    with open(settingsFile, 'r+') as settings_file:
        settings = json.load(settings_file)
        n = 0
        for i in settings[sløyfe]['devices']:
            if i['device_eui'] == device_eui:
                del settings[sløyfe]['devices'][n]
            n+=1
        settings_file.seek(0)
        settings_file.truncate(0) # Clear file
        json.dump(settings, settings_file)

def add_sløyfe(sløyfe):
    data = {sløyfe : 
                {'devices' : [],
                'alarm_values' : []}
            }
    with open(settingsFile, 'r+') as settings_file:
        settings = json.load(settings_file)
        settings.update(data)
        settings_file.seek(0)
        json.dump(settings, settings_file)

def remove_sløyfe(sløyfe):
    with open(settingsFile, 'r+') as settings_file:
        settings = json.load(settings_file)
        #del settings[sløyfe]
        settings.pop(sløyfe, None)
        settings_file.seek(0)
        settings_file.truncate(0) #clear file
        json.dump(settings, settings_file)

def change_alarm_values(sløyfe, min_value, max_value):
    alarm_values = {'min_val':min_value, 'max_val': max_value}
    with open(settingsFile, 'r+') as settings_file:
        settings = json.load(settings_file)
        settings[sløyfe]['alarm_values'] = alarm_values
        settings_file.seek(0)
        settings_file.truncate(0) #clear file
        json.dump(settings, settings_file)

def get_alarms(sløyfe):
    alarms = []
    with open(settingsFile) as json_file:
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

    # lag alle mulige rader i tabellen, vis bare de som har tilskrevet enhet
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

def confirm_controller_buttons(button_id, button_collapse_id):
    button_confirm_controller = dbc.Button("Bekreft", color='success', id=button_id)
    button_confirm_controller_collapse = dbc.Collapse(button_confirm_controller, id=button_collapse_id, is_open=False, className='collapsing-no-slide-animation')
    return button_confirm_controller_collapse

def manual_actuation_input():
    manual_actuation_input_field_collapse = dbc.Collapse([dbc.Row([
        dbc.Col(html.P("Manuelt pådrag: [%]", id='manual-actuation-input-label'), width=6),
        dbc.Col(dbc.Input(type='number', step=0.1, id='manual-actuation-input', value=controller1.get_u_tot()), width=2),
        dbc.Col(confirm_controller_buttons('manual-actuation-confirm-button', 'manual-actuation-confirm-button-collapse')),
    ], form=True)
    ], id='manual-actuation-input-field-collapse', is_open=False, className='collapsing-no-slide-animation')
    return manual_actuation_input_field_collapse

def controller_settings():
    controller_settings = html.Div([
        dbc.Row([
            html.H2("Regulator-innstillinger"),
        ]),
        dbc.Row([
            html.P(id='manual-actuation-dummy', children="Heat trace is on")
        ]),
        dbc.Row([
            dbc.Col(html.P("Automatisk AV/PÅ-styring", id='auto-actuation-label'), width=6),
            dbc.Col(dbc.Checklist(options=[{'value': True}], id='auto-actuation-checklist', switch=True)),
        ], form=True),
        dbc.Row([
            dbc.Col(html.P("Manuell styring", id='manual-actuation-label'), width=6),
            dbc.Col(dbc.RadioItems(options=[
                {'label': "AV", 'value': False, 'disabled': False},
                {'label': "PÅ", 'value': True, 'disabled': False},
            ], id='manual-actuation-radioitems', inline=True)),
        ], form=True),
        dbc.Row([
            dbc.Col(html.P("Regulatormodus", id='controller-mode-label'), width=6),
            dbc.Col(dbc.RadioItems(options=[
                {'label': "Auto", 'value': 'Auto'},
                {'label': "Manuell", 'value': 'Manual'},
            ], id='controller-mode-radioitems', inline=True, value=controller1.mode)),
        ], form=True),
        dbc.Row([
            dbc.Col(manual_actuation_input())
        ], form=True),
        dbc.Row([
            dbc.Col(html.P("Setpunkt: [°C]", id='setpoint-label'), width=6),
            dbc.Col(dbc.Input(type='number', step=0.1, id='setpoint-input', value=controller1.setpoint), width=2),
            dbc.Col(confirm_controller_buttons('setpoint-confirm-button', 'setpoint-confirm-button-collapse')),
        ], form=True),
        dbc.Row([
            dbc.Col(html.P("Proporsjonalforsterkning, Kp:", id='Kp-label'), width=6),
            dbc.Col(dbc.Input(type='number', step=0.01, id='Kp-input', value=controller1.Kp), width=2),
            dbc.Col(confirm_controller_buttons('Kp-confirm-button', 'Kp-confirm-button-collapse')),
        ], form=True),
        dbc.Row([
            dbc.Col(html.P("Integraltid, Ti [s]:", id='Ti-label'), width=6),
            dbc.Col(dbc.Input(type='number', id='Ti-input', value=controller1.Ti), width=2),
            dbc.Col(confirm_controller_buttons('Ti-confirm-button', 'Ti-confirm-button-collapse')),
        ], form=True),
        dbc.Row([
            dbc.Col(html.P("Dutycycle [min]:", id='dutycycle-label'), width=6),
            dbc.Col(dbc.Input(type='number', step=0.1, id='dutycycle-input', value=controller1.get_dutycycle()), width=2),
            dbc.Col(confirm_controller_buttons('dutycycle-confirm-button', 'dutycycle-confirm-button-collapse')),
        ], form=True),
    ])
    return controller_settings

def get_alarm_settings_inputs(chosen_sløyfe):
    print("Running get alarms input")
    curr_alarm_val = get_alarms(chosen_sløyfe)
    setting_inputs = html.Div([
        dbc.Row([
            dbc.Col(html.P("Max. temperatur: [°C]"), width=4),
            dbc.Col(dbc.Input(type='number', step=1, value=curr_alarm_val[1], id='max-temp-input',), width=2)
        ]),
        dbc.Row([
            dbc.Col(html.P("Min. temperatur: [°C]"), width=4),
            dbc.Col(dbc.Input(type='number', step=1, value=curr_alarm_val[0], id='min-temp-input',), width=2)
        ]),
    ])
    return setting_inputs

def get_alarm_settings(chosen_sløyfe):
    alarm_settings_div = [
        dbc.Row([html.H2("Alarm innstillinger")], className='mt-5'),
        html.Div(get_alarm_settings_inputs(chosen_sløyfe), id='alarm-settings'),
        dbc.Row(
            dbc.Collapse(dbc.Button("Oppdater alarm innstillinger", id='button-alarm-confirm'), id='collapse-alarm-confirm', is_open=False)
        )
    ]
    return alarm_settings_div

layout = html.Div([
    header,
    dbc.Container([
        dbc.Row([dbc.Col(html.Div(id='site-title-div'))]),
        dbc.Row(className='mt-3', children=[
            dbc.Col([
                dbc.Row(html.H2("Enheter i sløyfen")),
                dbc.Row(html.Div(html.Div(id='table-div'), id='table', className='tableFixHead')),
                dbc.Row([add_device_button()]),
                dbc.Row([confirm_buttons()])
            ]),
            dbc.Col([    
                controller_settings(),
                html.Div(id='alarm-settings-div'),
                ])
            ])
    ]),# Container
    dcc.Interval(id='interval-component', interval=5000, n_intervals=0),
    ])# Div


def callbacks(app):
    layout_callbacks(app)

    update_sløyfe_callback(app, [['site-title-div', get_site_title],
                                 ['table-div', get_settings_table],
                                 ['alarm-settings-div', get_alarm_settings]])

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
        ],
        [State(component_id='collapse-alarm-confirm', component_property='is_open'),
        State(component_id='url', component_property='pathname'),
        ])
    def show_confirm_alarm_settings(max_temp, min_temp, is_open, pathname):

        chosen_sløyfe = get_sløyfe_from_pathname(pathname)

        # hvis oppdater knappen bare når veriden er forandret
        curr_alarm_val = get_alarms(chosen_sløyfe)
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
        State(component_id='url', component_property='pathname'),
        ])
    def update_alarms(button_click, min_temp, max_temp, pathname):
        print("Running update alarm")
        chosen_sløyfe = get_sløyfe_from_pathname(pathname)

        ctx = dash.callback_context
        triggered_button = ctx.triggered[0]['prop_id'].split('.')[0]

        if triggered_button == 'button-alarm-confirm':
            change_alarm_values(chosen_sløyfe, min_temp, max_temp)
            return get_alarm_settings_inputs(chosen_sløyfe)
        else:
            return get_alarm_settings_inputs(chosen_sløyfe)

    # Oppdatering a referanse fra input
    @app.callback(
        Output(component_id='setpoint-confirm-button-collapse', component_property='is_open'),
        [
            Input(component_id='setpoint-input', component_property='value'),
            Input(component_id='setpoint-confirm-button', component_property='n_clicks'),
        ]
    )
    def display_setpoint_confirm(setpoint_input, button_clicks):
        global prew_setpoint_confirm_count
        if (button_clicks == None):
            prew_setpoint_confirm_count = 0
            if (setpoint_input == controller1.setpoint):
                return False
            else:
                return True
        elif (button_clicks > prew_setpoint_confirm_count):
            prew_setpoint_confirm_count = button_clicks
            controller1.update_setpoint(setpoint_input)
            return False
        return True

    # Oppdatering av forsterkningsfaktor Kp fra input
    @app.callback(
        Output(component_id='Kp-confirm-button-collapse', component_property='is_open'),
        [
            Input(component_id='Kp-input', component_property='value'),
            Input(component_id='Kp-confirm-button', component_property='n_clicks'),
        ]
    )
    def display_Kp_confirm(Kp_input, button_clicks):
        global prew_Kp_confirm_count
        if (button_clicks == None):
            prew_Kp_confirm_count = 0
            if (Kp_input == controller1.Kp):
                return False
            else:
                return True
        elif (button_clicks > prew_Kp_confirm_count):
            prew_Kp_confirm_count = button_clicks
            controller1.Kp = Kp_input
            print("New gain: {}".format(Kp_input))
            return False
        return True

    # Oppdatering av integraltid Ti fra input
    @app.callback(
        Output(component_id='Ti-confirm-button-collapse', component_property='is_open'),
        [
            Input(component_id='Ti-input', component_property='value'),
            Input(component_id='Ti-confirm-button', component_property='n_clicks'),
        ]
    )
    def display_Ti_confirm(Ti_input, button_clicks):
        global prew_Ti_confirm_count
        if (button_clicks == None):
            prew_Ti_confirm_count = 0
            if (Ti_input == controller1.Ti):
                return False
            else:
                return True
        elif (button_clicks > prew_Ti_confirm_count):
            prew_Ti_confirm_count = button_clicks
            controller1.Ti = Ti_input
            print("New integral time: {} sekunds".format(Ti_input))
            return False
        return True

    # Oppdatering av dutycycle fra input
    @app.callback(
        Output(component_id='dutycycle-confirm-button-collapse', component_property='is_open'),
        [
            Input(component_id='dutycycle-input', component_property='value'),
            Input(component_id='dutycycle-confirm-button', component_property='n_clicks'),
        ]
    )
    def display_dutycycle_confirm(dutycycle_input, button_clicks):
        global prew_dutycycle_confirm_count
        if (button_clicks == None):
            prew_dutycycle_confirm_count = 0
            if (dutycycle_input == controller1.get_dutycycle()):
                return False
            else:
                return True
        elif (button_clicks > prew_dutycycle_confirm_count):
            prew_dutycycle_confirm_count = button_clicks
            controller1.set_dutycycle(dutycycle_input)
            return False
        return True
    
    # Oppdatering av manuelt pådrag fra input
    @app.callback(
        Output(component_id='manual-actuation-confirm-button-collapse', component_property='is_open'),
        [
            Input(component_id='manual-actuation-input', component_property='value'),
            Input(component_id='manual-actuation-confirm-button', component_property='n_clicks'),
        ]
    )
    def display_dutycycle_confirm(manual_actuation_input, button_clicks):
        global prew_manual_actuation_confirm_count
        if (button_clicks == None):
            prew_manual_actuation_confirm_count = 0
            if (manual_actuation_input == controller1.get_u_tot()):
                return False
            else:
                return True
        elif (button_clicks > prew_manual_actuation_confirm_count):
            prew_manual_actuation_confirm_count = button_clicks
            controller1.set_u_tot(manual_actuation_input)
            return False
        return True

    # Aktivering/deaktivering av automatisk av/på-styring
    @app.callback(
        [
            Output(component_id='manual-actuation-radioitems', component_property='options'),
            Output(component_id='manual-actuation-radioitems', component_property='value'),
        ],
        [
            Input(component_id='auto-actuation-checklist', component_property='value'),
        ]
    )
    def enable_disable_manual_actuation(auto_actuation):
        outputState = get_output_state('heatTrace1')[0]
        print('Tilstand på "auto_actuation": {}, "outputState": {}'.format(auto_actuation, outputState))
        if auto_actuation:
            print("Starter automatisk av-på-styring.")
            controller1.start()
            return ([
                {'label': "AV", 'value': False, 'disabled': True},
                {'label': "PÅ", 'value': True, 'disabled': True}
            ], not outputState)
        else:
            controller1.stop()
            print("Stopper automatisk av-på-styring.")
            return ([
                {'label': "AV", 'value': False, 'disabled': False},
                {'label': "PÅ", 'value': True, 'disabled': False}
            ], not outputState)
        
    # Manuell av/på-styring
    @app.callback(
        Output(component_id='manual-actuation-dummy', component_property='children'),
        [
            Input(component_id='manual-actuation-radioitems', component_property='value'),
        ],
        [
            State(component_id='auto-actuation-checklist', component_property='value')
        ]
    )
    def activate_deactivate_heat_trace(on_off, auto):
        outputState = get_output_state('heatTrace1')[0]
        print("on_off: {}, auto: {}, outputState: {}".format(on_off, auto, outputState))
        if ((on_off == None) or (auto == None)):
            return "Oppdaterer..."
        if (on_off and not auto and outputState):
            print("Aktiverer varmekabel")
            return activateHeatTrace('heatTrace1')
        elif (not on_off and not auto and not outputState):
            print("Deaktiverer varmekabel")
            return deactivateHeatTrace('heatTrace1')
        else:
            return "Siden er oppdatert"

    # Regulatormodus
    @app.callback(
        Output(component_id='manual-actuation-input-field-collapse', component_property='is_open'),
        [
            Input(component_id='controller-mode-radioitems', component_property='value'),
        ],
        [
            State(component_id='manual-actuation-input', component_property='value')
        ]
    )
    def show_hide_manual_actuation_field(mode, manual_actuation_input):
        print("Innkommende modus: {}".format(mode))
        if (mode != controller1.mode):
            controller1.change_mode(mode, manual_actuation_input)
        if (mode == 'Auto'):
            return False
        else:
            return True

    # Oppdater input/verdier hvert sekund
    @app.callback(
        [
            Output(component_id='auto-actuation-checklist', component_property='value'),
            Output(component_id='controller-mode-radioitems', component_property='value'),
            Output(component_id='manual-actuation-input', component_property='value'),
            Output(component_id='setpoint-input', component_property='value'),
            Output(component_id='Kp-input', component_property='value'),
            Output(component_id='Ti-input', component_property='value'),
            Output(component_id='dutycycle-input', component_property='value'),
        ],
        [
            Input(component_id='interval-component', component_property='n_intervals'),
        ]
    )
    def update_input_fields(value):
        print("Oppdaterer inputs")
        if (controller1.run_actuation == True):
            auto = [True]
        else:
            auto = []
        print("Tilstand på auto: {}".format(auto))
        return (
            auto,
            controller1.mode,
            controller1.get_u_tot(),
            controller1.setpoint,
            controller1.Kp,
            controller1.Ti,
            controller1.dutycycle,
        )