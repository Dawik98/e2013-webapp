"""
innstillinger.py inneholder:
    - layout og callbacks som brukes på Innstilling siden
    - funksjoner for å forandre innstilinger som lagres i settings.txt
    - funksjoner for å lese data fra settings.txt filen
"""

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc 
import dash_html_components as html 
from dash.exceptions import PreventUpdate
from dash.dash import no_update
import dash_bootstrap_components as dbc
from mqttCommunication import claimMeterdata, activateHeatTrace, deactivateHeatTrace, get_output_state, get_controller

import json
import re
from itertools import zip_longest
from datetime import datetime, timedelta

# GLOBALE VARIABLER
prew_setpoint_confirm_count = 0
prew_Kp_confirm_count = 0
prew_Ti_confirm_count = 0
prew_dutycycle_confirm_count = 0
prew_actuation_confirm_count = 0

# Velges avhengig av om appen kjøres lokalt eller i Azure
#settingsFile = 'settings.txt' # Azure
settingsFile = 'app/settings.txt' # Lokalt

def print_settings():
    """
    print_settings printer innstillinger til konsolen som ligger i 'settings.txt' på en lesbar måte
    """

    with open(settingsFile) as json_file:
        data = json.load(json_file)
        print(json.dumps(data, indent=4))

def get_settings():
    """
    get_settings returnerer innstillinger som ligger i 'settings.txt' 

    Returns
    -------
    dictionary
        alle sløyfer og den sine innstillinger. Hver sløyfe innstilinger har følgende struktur:
        {'sløyfe_navn' : {'devices' : [ {'device_eui' : string -- eui til enheten, 'device_type' : string -- type enhet}, ...],
                        'alarm_values' : {'min_val' : int -- laveste alarm grense, 'max_val' : int -- høyeste alarm grense}}
    """

    with open(settingsFile) as json_file:
        data = json.load(json_file)
        return data

def get_sløyfer():
    """
    get_sløyfer returnerer alle sløyfer som ligger i 'settings.txt' filen

    Returns
    -------
    list
        liste med navn til alle sløyfer
    """

    sløyfer = []
    with open(settingsFile) as json_file:
        data = json.load(json_file)
        for key, value in data.items():
            sløyfer.append(key)
    return sløyfer

def get_devices():
    """
    returnerer alle enheter til decoder() for å kunne bestemme devicePlacement og deviceType

    Returns
    -------
    dict
        En dictionary med alle enheter med eui som 'key' og liste med plassering og type som 'value'
        {'deviceEui' : ['enhetens plasering', 'type enhet'], ...}
    """

    devices = {}
    with open(settingsFile) as json_file:
        data = json.load(json_file)
        for sløyfe in data:
            for device in data[sløyfe]['devices']:
                deviceType = device['deviceType']
                if (deviceType == 'Temperatur sensor'):
                    deviceType = 'tempSensor'
                elif (deviceType == 'Power Switch'):
                    deviceType = 'powerSwitch'
                devices[device['device_eui']] = [sløyfe, deviceType]
    return devices

def get_temp_sensors_in_placement(devicePlacement):
    """
    Funksjonen returnerer en liste med enhets-EUI-er for enheter tilknyttet aktuell varmekrets.
    """
    devicesInPlacement = get_settings()[devicePlacement]['devices']
    devices = []
    for i in range(0, len(devicesInPlacement)):
        if (devicesInPlacement[i]['deviceType'] == "Temperatur sensor"):
            devices.append(devicesInPlacement[i]['device_eui'])
    return devices


def add_device(sløyfe, device_eui, device_type):
    """
    add_device legger til en ny enhet i valgt sløfe i 'settings.txt' fila

    Parameters
    ----------
    sløyfe : string
        navn på sløyfen hvor ny enhets skal legges til
    device_eui : string
        eui til den nye enheten, den samme som registreres i gatewayen
    device_type : string
        type enhet som legges til, foreløpig Temperatur Sensor eller Power Switch
    """

    device_data = {'device_eui':device_eui, 'deviceType': device_type}
    with open(settingsFile, 'r+') as settings_file:
        settings = json.load(settings_file)
        settings[sløyfe]['devices'].append(device_data)
        settings_file.seek(0)
        json.dump(settings, settings_file)

def remove_device(sløyfe, device_eui):
    """
    remove_device sletter en enhet fra 'settings.txt' fila

    Parameters
    ----------
    sløyfe : string
        navn på hvilken sløyfe enheten skal fjernes ifra
    device_eui : string
        eui til enheten som skal slettes
    """

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
    """
     add_sløyfe legger til en ny sløyfe i 'settings.txt' filen

    Parameters
    ----------
    sløyfe : string
        navn på sløyfen som skal legges til
    """

    data = {sløyfe : 
                {'devices' : [],
                'alarm_values' : {"min_val":None, "max_val":None}}
            }
    with open(settingsFile, 'r+') as settings_file:
        settings = json.load(settings_file)
        settings.update(data)
        settings_file.seek(0)
        json.dump(settings, settings_file)

def remove_sløyfe(sløyfe):
    """
    remove_sløyfe sletter en sløyfe i 'settings.txt' filen

    Parameters
    ----------
    sløyfe : string
        navn på sløyfen som skal slettes
    """

    with open(settingsFile, 'r+') as settings_file:
        settings = json.load(settings_file)
        del settings[sløyfe]
        #settings.pop(sløyfe, None)
        settings_file.seek(0)
        settings_file.truncate(0) #clear file
        json.dump(settings, settings_file)

def change_alarm_values(sløyfe, min_value, max_value):
    """
    change_alarm_values forandrer på alarmerdier som ligger i 'settings.txt' filen

    Parameters
    ----------
    sløyfe : string
        navn på sløyfen som det skal byttes alarm verdier til
    min_value : int
        laveste alarm grense
    max_value : int
        høyeste alarm grense
    """

    alarm_values = {'min_val':min_value, 'max_val': max_value}
    with open(settingsFile, 'r+') as settings_file:
        settings = json.load(settings_file)
        settings[sløyfe]['alarm_values'] = alarm_values
        settings_file.seek(0)
        settings_file.truncate(0) #clear file
        json.dump(settings, settings_file)

def get_alarms(sløyfe):
    """
    get_alarms returnerer alarmverdier til valgt sløyfe

    Parameters
    ----------
    sløyfe : string
        navn på sløfen man skal hente alarmer til

    Returns
    -------
    list
        liste med alarmverdier på formen: [laveste_grense, høyeste grense]
    """

    alarms = []
    with open(settingsFile) as json_file:
        data = json.load(json_file)
        for key, value in data[sløyfe]['alarm_values'].items():
            alarms.append(value)
        print(alarms)
    return alarms

def get_device_status(sløyfe, device_eui):
    """
    get_device_status returnerer status til enheten basert på hvor lenge siden den har 
    sendt siste data. I tillegg viser den batteriprosent hvis enheten er en temperatursensor.

    Parameters
    ----------
    sløyfe : string
        sløyfe som enehten ligger i
    device_eui : string
        enehetens eui

    Returns
    -------
    list 
        liste med dash_html_components: html.I font-awesome icon som indikerer status
                                        html.I batteri icon og text med batteri prosent
    """

    from cosmosDB import read_from_db

    # hent sist sendte data til enheten
    try:
        query = "SELECT TOP 1 * FROM {0} WHERE {0}.deviceEui = '{1}' ORDER BY {0}.timeReceived DESC".format(sløyfe, device_eui)
        data = read_from_db(sløyfe, query)
        data = data[0]
    except:
        return "Ingen data"

    # Batteri label blir tom hvis enheten er ikke en temperatur sensor
    battery_label = [""]
    if data['deviceType'] == 'tempSensor':
        # Lager en label som bestpr av batteri icon og patteriprosenten
        battery = "{}%".format(round(data['batteryLevel']))
        battery_icon = html.I(className="fas fa-battery-three-quarters fa-lg ml-3 mr-1")
        battery_label = [battery_icon, battery]

    # Finner ut hvor lenge siden data ble sendt
    message_time = data['timeReceived']
    message_time = datetime.strptime(message_time, '%Y-%m-%d %H:%M:%S')
    now = datetime.now()
    time_diff = now-message_time 

    # Hvis enheten har sendt noe på 3 timer -> status grønn
    if time_diff < timedelta(hours=3):
        title = "Siste data ble sendt: {}".format(message_time)
        icon_connection = html.I(className="fas fa-circle fa-lg", style={'color':'#86d01b'}, title=title)
        label = [icon_connection] + battery_label
        return label
    # Hvis enheten har ikke sendt noe på 3 timer -> status rødt
    else:
        title = "Ingen nye data siden: {}".format(message_time)
        icon_no_connection = html.I(className="fas fa-circle fa-lg", style={'color':'red'}, title=title)
        label = [icon_no_connection] + battery_label
        return label

#---------------------------------------------------- Site components --------------------------------------------------------------------

def make_id_dict():
    """
    make_id_dict lager 20 slettknapper med hver sin unik ID som skal brukes til å kunne slette enheter fra enhets-tabellen. 
    Grunnen til at alle må defineres på forhånd er at alle id-er/html elementer må eksistere når nettsiden startes for at callback skal kunne kjøres.
    Det kan derfor være nødvendig å definere flere  kanpper hvis sløfen skal ha mer enn 20 enheter

    Returns
    -------
    dict
        remove_buttons_ids innehloder id-er til alle knapper som 'keys' og hvilken enhet de er tilknyttet (eui) som 'value', None i utgangspunktet
        
    dict
        remove_buttons {dictionary} -- innehloder id-er til alle knapper som 'keys' og selve knappen i html som 'value'
        remove_buttons_ids innehloder id-er til alle knapper som 'keys' og hvilken enhet de er tilknyttet (eui) som 'value', None i utgangspunktet
    """

    remove_buttons_ids = {}
    remove_buttons = {}

    for i in range(20):
        id_ = "delete-row-{}".format(i+1)
        remove_buttons_ids[id_] = None
        # Hver kanpp er en font-awesome icon:
        remove_buttons[id_] = html.I(className="fas fa-window-close fa-pull-right fa-lg", id=id_)
    
    return remove_buttons_ids, remove_buttons
    
# lag alle slett knappene når nettsiden startes
remove_buttons_ids, remove_buttons = make_id_dict()


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
    site_title = html.Div(html.H1("Innstillinger for {}".format(chosen_sløyfe), id="site-title"), className="page-header") 
    return site_title


def get_settings_table(chosen_sløyfe):
    """
    get_settings_table lager en tabell med alle enheter i den valgte sløyfen. Tabellen inneholder enhetens eui, type enhet og dens status.
    I tabellen er det også en rad vises når man skal legge til en ny enhet.

    Parameters
    ----------
    chosen_sløyfe : string
        navn på sløyfen som er valgt

    Returns
    -------
    dash_bootstrap_components
        dbc.Tabel med alle enheter i sløyfen
    """

    # Definnere bredden som brukes på status kolonnen
    small_coll = {'width':'120px'}

    settings = get_settings()
    settings = settings[chosen_sløyfe]['devices']
    #print(settings)

    table_header = [html.Thead(html.Tr([html.Th("Enhetens eui"), html.Th("Enhet"), html.Th("Status", style=small_coll)]))]
    # Liste som vil inneholde alle rader
    table_rows = []

    # Lager egen rad som skal vises når man vil legge til en ny eneht
    add_eui = dbc.Input(placeholder="Skriv inn enhetens eui", type='text', id="add-eui")
    device_types = [dbc.DropdownMenuItem("Temperatur sensor", id='tempSensor'),
                    dbc.DropdownMenuItem("Power switch", id='powerSwitch')]
    add_type = dbc.DropdownMenu(device_types, label="Velg enhet type", id="add-type")#, toggleClassName="btn-outline-secondary")
    add_device_row = dbc.Collapse(html.Tr([html.Td(add_eui), html.Td(add_type), html.Td(style=small_coll)]), id='add-row-collapse')#, is_open=False)

    # lag alle mulige rader i tabellen, vis bare de som har tilskrevet enhet
    for (key, status), setting_item in zip_longest(remove_buttons_ids.items(), settings):

        # hvis det finnes innstiliinger for enhet
        if setting_item:
            deviceEui = setting_item["device_eui"]
            deviceType = setting_item["deviceType"]

            # henter knappene som lages i make_id_dict()
            delete_button = remove_buttons[key]
            remove_buttons_ids[key]=deviceEui # skriver hvilken enhet knappen tilhører 

            # teksten som skal vises i tabellen
            if deviceType == "tempSensor":
                deviceType = "Temperatur sensor"
            elif deviceType == "powerSwitch":
                deviceType = "Power switch"

            dev_status = get_device_status(chosen_sløyfe, deviceEui)

            row = html.Tr([html.Td(deviceEui), html.Td([deviceType, delete_button]), html.Td(dev_status, style=small_coll)])
            table_rows.append(row)
        
        # hvis det finnes ikke flere enheter lag tome raader
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
    """
    add_device_button lager en knapp som brukes til å åpne rad for å legge til ny enhet (se callbacks)

    Returns
    -------
    dash_bootstrap_components
        dbc.Collapse som inneholder dbc.Button
    """

    button = dbc.Button("Legg til ny enhet", id="add-device-button")
    button_collapse = dbc.Collapse(button, id='add-device-button-collapse', is_open=True, className="collapsing-no-slide-animation")
    return button_collapse

def confirm_buttons():
    """
    confirm_buttons lager to knapper en for å legge til en enhet og en for å avbryte operasjonen. Begge to vil lukke
    raden for å legge til ny enhet (se calback)

    Returns
    -------
    dash_bootstrap_components
        dbc.Collapse som  inneholder de to knappene
    """

    button_confirm = dbc.Button("Legg til", id="confirm-add-device-button", color='success', className='mr-2')
    button_cancel = dbc.Button("Avbryt", id="cancel-add-device-button", color='danger', className='mr-2')
    button_collapse = dbc.Collapse(html.Div([button_confirm, button_cancel]), id='confirm-add-device-button-collapse', is_open=False, className="collapsing-no-slide-animation")
    return button_collapse

def confirm_controller_buttons(button_id, button_collapse_id):
    """
    Funksjonen genererer en bekreftelsesknapp som kan kollapses
    """
    button_confirm_controller = dbc.Button("Bekreft", color='success', id=button_id)
    button_confirm_controller_collapse = dbc.Collapse(button_confirm_controller, id=button_collapse_id, is_open=False, className='collapsing-no-slide-animation')
    return button_confirm_controller_collapse

def controller_settings(chosen_sløyfe):
    """
    All innstilling av regulator i layout-en
    """
    try:
        controller = get_controller(chosen_sløyfe)
    except:
        print("No controller found")
        return ""

    if (controller.run_actuation == True):
        auto = [True]
    else:
        auto = []
    if (controller.mode == 'Auto'):
        disabled = True
    else:
        disabled = False
    controller_settings = html.Div([
        dbc.Row([
            html.H2("Regulator-innstillinger"),
        ]),
        dbc.Row([
            html.P(id='manual-actuation-dummy', children="Heat trace is on")
        ]),
        dbc.Row([
            dbc.Col(html.P("Automatisk AV/PÅ-styring", id='auto-actuation-label'), width=6),
            dbc.Col(dbc.Checklist(options=[{'value': True}], id='auto-actuation-checklist', switch=True, value=auto)),
        ], form=True),
        dbc.Row([
            dbc.Col(html.P("Manuell styring", id='manual-actuation-label'), width=6),
            dbc.Col(dbc.RadioItems(options=[
                {'label': "AV", 'value': False, 'disabled': False},
                {'label': "PÅ", 'value': True, 'disabled': False},
            ], id='manual-actuation-radioitems', inline=True, value=(not get_output_state(chosen_sløyfe)[0]))),
        ], form=True),
        dbc.Row([
            dbc.Col(html.P("Regulatormodus", id='controller-mode-label'), width=6),
            dbc.Col(dbc.RadioItems(options=[
                {'label': "Auto", 'value': 'Auto'},
                {'label': "Manuell", 'value': 'Manual'},
            ], id='controller-mode-radioitems', inline=True, value=controller.mode)),
        ], form=True),
        dbc.Row([
            dbc.Col(html.P("Pådrag: [%]", id='actuation-label'), width=6),
            dbc.Col(dbc.Input(type='number', step=0.1, id='actuation-input', value=controller.get_u_tot(), disabled=disabled), width=2),
            dbc.Col(confirm_controller_buttons('actuation-confirm-button', 'actuation-confirm-button-collapse')),
        ], form=True),
        dbc.Row([
            dbc.Col(html.P("Setpunkt: [°C]", id='setpoint-label'), width=6),
            dbc.Col(dbc.Input(type='number', step=0.1, id='setpoint-input', value=controller.setpoint), width=2),
            dbc.Col(confirm_controller_buttons('setpoint-confirm-button', 'setpoint-confirm-button-collapse')),
        ], form=True),
        dbc.Row([
            dbc.Col(html.P("Proporsjonalforsterkning, Kp:", id='Kp-label'), width=6),
            dbc.Col(dbc.Input(type='number', step=0.01, id='Kp-input', value=controller.Kp), width=2),
            dbc.Col(confirm_controller_buttons('Kp-confirm-button', 'Kp-confirm-button-collapse')),
        ], form=True),
        dbc.Row([
            dbc.Col(html.P("Integraltid, Ti [s]:", id='Ti-label'), width=6),
            dbc.Col(dbc.Input(type='number', step=10, id='Ti-input', value=controller.Ti), width=2),
            dbc.Col(confirm_controller_buttons('Ti-confirm-button', 'Ti-confirm-button-collapse')),
        ], form=True),
        dbc.Row([
            dbc.Col(html.P("Dutycycle [min]:", id='dutycycle-label'), width=6),
            dbc.Col(dbc.Input(type='number', step=0.1, id='dutycycle-input', value=controller.get_dutycycle()), width=2),
            dbc.Col(confirm_controller_buttons('dutycycle-confirm-button', 'dutycycle-confirm-button-collapse')),
        ], form=True, className='mb-5'),
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
        dbc.Row([html.H2("Alarm innstillinger")]),
        html.Div(get_alarm_settings_inputs(chosen_sløyfe), id='alarm-settings'),
        dbc.Row(
            dbc.Collapse(dbc.Button("Oppdater alarm innstillinger", id='button-alarm-confirm'), id='collapse-alarm-confirm', is_open=False)
        )
    ]
    return alarm_settings_div

def serve_layout():
    """
    Layout-en genereres i en egen funksjon slik at den kjører hver gang nettsiden lastes inn på nytt
    """
    from dashApps.layout import header
    layout = html.Div([
        header,
        dbc.Container([
            dbc.Row([
                dbc.Col(html.Div(id='site-title-div'))
            ]),
            dbc.Row(className='mt-3', children=[
                dbc.Col([
                    dbc.Row(html.H2("Enheter i sløyfen")),
                    dbc.Row(html.Div(html.Div(id='table-div'), id='table', className='tableFixHead')),
                    dbc.Row([add_device_button()]),
                    dbc.Row([confirm_buttons()]),
                ]),
                dbc.Col([
                    html.Div(html.Div(id='controller-settings-div'), id='controller-settings'),
                    html.Div(id='alarm-settings-div'),
                ])
            ]),
        ], id='main-container'),# Container
        dcc.Interval(id='interval-component', interval=2000, n_intervals=0),
    ])# Div
    return layout

layout = serve_layout

def callbacks(app):
    """
    callbacks holder alle callbacks som brukes på denne siden

    Parameters
    ----------
    app : dash.Dash
        dashApp for denne siden

    """

    from dashApps.layout import update_sløyfe_callback, get_sløyfe_from_pathname
    from dashApps.layout import callbacks as layout_callbacks
    layout_callbacks(app)

    update_sløyfe_callback(app, [['site-title-div', get_site_title],
                                 ['table-div', get_settings_table],
                                 ['alarm-settings-div', get_alarm_settings],
                                 ['controller-settings-div', controller_settings]])

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
    def display_confirm_buttons(click_add_device, click_confirm_add, click_cancel_add, is_add_button_open, is_confirm_buttons_open):
        if click_add_device or click_confirm_add or click_cancel_add:
            if is_add_button_open:
                return True
            if is_confirm_buttons_open:
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
        # kobler id til knappen med det som skal stå på kanppen
        id_lookup = {'tempSensor':'Temperatur sensor', 'powerSwitch':'Power Switch', 'cancel-add-device-button':'Velg enhet type', 'confirm-add-device-button':'Velg enhet type'}

        try:
            ctx = dash.callback_context

            button_id = ctx.triggered[0]["prop_id"].split(".")[0] #finner ut hva som trigged callback
            label_clicked = id_lookup[button_id] #finner ut label som skal stå på knappen etter at knappen trykkes

            if (click_tempSensor is None and click_powerSwitch is None) or not ctx.triggered:
            # hvis ingen av knappene bly trykket returner standard text
                return "Velg enhet type"

            return label_clicked
        except:
            return "Velg enhet type"
        

    # lager alle slett-knapp inputs som skal brukes i neste callback
    def delete_buttons_inputs():
        inputs = []

        for key, status in remove_buttons_ids.items():
            inputs.append(Input(component_id=key, component_property='n_clicks'))
        #print(inputs)
        return inputs

    # Oppdater tabellen med enheter når ny enhet legges til
    @app.callback(
        Output(component_id='table', component_property='children'),
        [Input(component_id='confirm-add-device-button', component_property='n_clicks')]+delete_buttons_inputs(),
        [State(component_id='add-eui', component_property='value'),
        State(component_id='add-type', component_property='label'),
        State(component_id='url', component_property='pathname'),
        ])
    def update_settings(click_confirm_add, *args, **kwargs):

        ctx = dash.callback_context
        # henter alle states og inputs til callbacken
        states = ctx.states
        inputs = ctx.inputs

        pathname = states['url.pathname']
        device_type = states['add-type.label']
        chosen_sløyfe = get_sløyfe_from_pathname(pathname) #bestemmer hvilken sløyfe som er valgt

        triggered_button = ctx.triggered[0]['prop_id'].split('.')[0]
        #print(ctx.triggered)
        #print('triggered by "{}" '.format(triggered_button))

        device_eui = states['add-eui.value']
        device_type = states['add-type.label']

        if triggered_button == None or ctx.triggered[0]['value'] == None:
            # kjører hvis nettsiden blir oppdatert
            return get_settings_table(chosen_sløyfe)
        elif triggered_button == 'confirm-add-device-button':
            # hvis ny enhet blir lagt til
            add_device(chosen_sløyfe, device_eui, device_type)
            if device_type == 'Power Switch':
                # hvis det legges til en powerSwitch, så lages det automatisk en regulator
                from mqttCommunication import createController
                createController(chosen_sløyfe)
            return get_settings_table(chosen_sløyfe)
        elif triggered_button != 'confirm-add-device-button':
            # hvis ingen enhet er lagt til så må callback være trigget av en slett knapp
            devices = get_devices()
            eui = remove_buttons_ids[triggered_button] #hent eui til enheten som skal slettes
            if 'powerSwitch' in  devices[eui]:
                #hvis det er en powerswitch slett regulator
                from mqttCommunication import deleteController
                deleteController(chosen_sløyfe)

            #print("Deleting"+eui)
            remove_device(chosen_sløyfe, eui)
            return get_settings_table(chosen_sløyfe)

    # Last inn innstillinger på nytt når en regulator blir lagt til eller slettet
    @app.callback(
        Output('controller-settings', 'children'),
        [Input('confirm-add-device-button', 'n_clicks')]+delete_buttons_inputs(),
        [State(component_id='add-type', component_property='label'),
        State('url', 'pathname')],
        )
    def update_controller_settings_div(*args):
        ctx = dash.callback_context
        states = ctx.states
        inputs = ctx.inputs

        triggered_by = ctx.triggered[0]['prop_id'].split('.')[0]

        pathname = states['url.pathname']
        chosen_sløyfe=get_sløyfe_from_pathname(pathname)

        if triggered_by == None or ctx.triggered[0]['value'] == None:
            raise PreventUpdate
        elif triggered_by == 'confirm-add-device-button' and states['add-type.label'] == 'Power Switch':
            from time import sleep
            sleep(0.5) # venter litt for å være sikker at regulator ble lagt til
            return controller_settings(chosen_sløyfe)
        elif 'delete' in triggered_by and 'powerSwitch' in get_devices()[remove_buttons_ids[triggered_by]]:
            from time import sleep
            sleep(0.5) # venter litt for å være sikker at regulator ble slettet
            print("updating_settings_window")
            return controller_settings(chosen_sløyfe)
        else:
            raise PreventUpdate
            
    # Disable power switch valget når man prøver å legge til ny enhet hvis det allerede finnes en regulator
    @app.callback(
        Output('powerSwitch', 'disabled'),
        [Input('add-device-button', 'n_clicks')],
        [State('url', 'pathname')])
    def disable_power_switch_choice(click, pathname):
        ctx = dash.callback_context
        chosen_sløyfe = get_sløyfe_from_pathname(pathname)
        settings = get_settings()
        devices = settings[chosen_sløyfe]['devices']

        regulator_in_sløyfe = False
        # Gå gjennom alle enheter i sløyfen og se om det finnes en power switch
        for device in devices:
            #print("devices i sløyfe: {}".format(device.values()))
            if 'Power Switch' in device.values():
                #print("Regulator i sløyfe!!!")
                return True

        if  ctx.triggered[0]['value'] == None:
            raise PreventUpdate
        else:
            return False

    # Vis skjul knappen for å endre alarm-verdier
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

        # vis knappen bare når veriden er forandret
        curr_alarm_val = get_alarms(chosen_sløyfe)
        if [min_temp, max_temp] == curr_alarm_val:
            return False
        else:
            #print ("max = {}; min = {}".format(max_temp, min_temp))
            return True

    # Oppdater alarmer når de nye blir godkjent med knapp
    @app.callback(
        Output(component_id='alarm-settings', component_property='children'),
        [Input(component_id='button-alarm-confirm', component_property='n_clicks'),
        ],
        [State(component_id='min-temp-input', component_property='value'),
        State(component_id='max-temp-input', component_property='value'),
        State(component_id='url', component_property='pathname'),
        ])
    def update_alarms(button_click, min_temp, max_temp, pathname):
        #print("Running update alarm")
        chosen_sløyfe = get_sløyfe_from_pathname(pathname)

        ctx = dash.callback_context

        if not ctx.triggered:
            raise PreventUpdate
            #return get_alarm_settings_inputs(chosen_sløyfe)
        else: 
            change_alarm_values(chosen_sløyfe, min_temp, max_temp)
            return get_alarm_settings_inputs(chosen_sløyfe)

    # Oppdatering av referanse fra input
    @app.callback(
        Output(component_id='setpoint-confirm-button-collapse', component_property='is_open'),
        [
            Input(component_id='setpoint-input', component_property='value'),
            Input(component_id='setpoint-confirm-button', component_property='n_clicks'),
        ],
        [
            State(component_id='url', component_property='pathname'),
        ]
    )
    def display_setpoint_confirm(setpoint_input, button_clicks, pathname):
        global prew_setpoint_confirm_count                                  # Definerer global tellevariabel
        chosen_sløyfe = get_sløyfe_from_pathname(pathname)                  # Bestemmer valgt sløyfe ut ifra pathname
        try:
            controller = get_controller(chosen_sløyfe)                      # Velger regulator avhengig av valgt sløyfe
        except:
            raise PreventUpdate
        if (button_clicks == None):                                         # button_clicks er None etter at siden lastes inn på nytt
            prew_setpoint_confirm_count = 0                                 # Resetter tellevariabelen
        elif (button_clicks > prew_setpoint_confirm_count):                 # Dersom knappen er trykt bekreftes setpunktet:
            print("New setpoint: {} °C".format(setpoint_input))
            prew_setpoint_confirm_count = button_clicks                     # Tellevariabel oppdateres
            controller.update_setpoint(setpoint_input)                      # Setpunkt skrives til regulatoren
            return False                                                    # Bekreftelsesknapp skjules etter bekreftelse
        if (setpoint_input == controller.setpoint):                         # Kontrollerer om setpunktet er forandret
            return False                                                    # Bekreftelsesknapp vises ikke dersom regulatorens setpunkt stemmer med input-verdien
        else:
            return True                                                     # Bekreftelsesknapp vises dersom setpunktet er forskjellig fra input-verdien

    # Oppdatering av forsterkningsfaktor Kp fra input
    @app.callback(
        Output(component_id='Kp-confirm-button-collapse', component_property='is_open'),
        [
            Input(component_id='Kp-input', component_property='value'),
            Input(component_id='Kp-confirm-button', component_property='n_clicks'),
        ],
        [
            State(component_id='url', component_property='pathname'),
        ]
    )
    def display_Kp_confirm(Kp_input, button_clicks, pathname):
        global prew_Kp_confirm_count                                        # Definerer global tellevariabel
        chosen_sløyfe = get_sløyfe_from_pathname(pathname)                  # Bestemmer valgt sløyfe ut ifra pathname
        try:
            controller = get_controller(chosen_sløyfe)                      # Velger regulator avhengig av valgt sløyfe
        except:
            raise PreventUpdate                  
        if (button_clicks == None):                                         # button_clicks er None etter at siden lastes inn på nytt
            prew_Kp_confirm_count = 0                                       # Resetter tellevariabelen
        elif (button_clicks > prew_Kp_confirm_count):                       # Dersom knappen er trykt bekreftes ny forsterkningsfaktor, Kp:
            print("New gain: {}".format(Kp_input))
            prew_Kp_confirm_count = button_clicks                           # Tellevariabel oppdateres
            controller.Kp = Kp_input                                        # Kp skrives til regulatoren
            return False                                                    # Bekreftelsesknapp skjules etter bekreftelse
        if (Kp_input == controller.Kp):                                     # Kontrollerer om Kp er forandret
            return False                                                    # Bekreftelsesknapp vises ikke dersom regulatorens Kp stemmer med input-verdien
        else:
            return True                                                     # Bekreftelsesknapp vises dersom Kp er forskjellig fra input-verdien
        
    # Oppdatering av integraltid Ti fra input
    @app.callback(
        Output(component_id='Ti-confirm-button-collapse', component_property='is_open'),
        [
            Input(component_id='Ti-input', component_property='value'),
            Input(component_id='Ti-confirm-button', component_property='n_clicks'),
        ],
        [
            State(component_id='url', component_property='pathname'),
        ]
    )
    def display_Ti_confirm(Ti_input, button_clicks, pathname):
        global prew_Ti_confirm_count                                        # Definerer global tellevariabel
        chosen_sløyfe = get_sløyfe_from_pathname(pathname)                  # Bestemmer valgt sløyfe ut ifra pathname
        try:
            controller = get_controller(chosen_sløyfe)                      # Velger regulator avhengig av valgt sløyfe
        except:
            raise PreventUpdate                         
        if (button_clicks == None):                                         # button_clicks er None etter at siden lastes inn på nytt
            prew_Ti_confirm_count = 0                                       # Resetter tellevariabelen
        elif (button_clicks > prew_Ti_confirm_count):                       # Dersom knappen er trykt bekreftes ny integraltid, Ti:
            print("New integral time: {} secunds".format(Ti_input))
            prew_Ti_confirm_count = button_clicks                           # Tellevariabel oppdateres
            controller.Ti = Ti_input                                        # Ti skrives til regulatoren
            return False                                                    # Bekreftelsesknapp skjules etter bekreftelse
        if (Ti_input == controller.Ti):                                     # Kontrollerer om Ti er forandret
            return False                                                    # Bekreftelsesknapp vises ikke dersom regulatorens Ti stemmer med input-verdien
        else:
            return True                                                     # Bekreftelsesknapp vises dersom Ti er forskjellig fra input-verdien

    # Oppdatering av dutycycle fra input
    @app.callback(
        Output(component_id='dutycycle-confirm-button-collapse', component_property='is_open'),
        [
            Input(component_id='dutycycle-input', component_property='value'),
            Input(component_id='dutycycle-confirm-button', component_property='n_clicks'),
        ],
        [
            State(component_id='url', component_property='pathname'),
        ]
    )
    def display_dutycycle_confirm(dutycycle_input, button_clicks, pathname):
        global prew_dutycycle_confirm_count                                 # Definerer global tellevariabel
        chosen_sløyfe = get_sløyfe_from_pathname(pathname)                  # Bestemmer valgt sløyfe ut ifra pathname
        try:
            controller = get_controller(chosen_sløyfe)                      # Velger regulator avhengig av valgt sløyfe
        except:
            raise PreventUpdate                    
        if (button_clicks == None):                                         # button_clicks er None etter at siden lastes inn på nytt
            prew_dutycycle_confirm_count = 0                                # Resetter tellevariabelen
        elif (button_clicks > prew_dutycycle_confirm_count):                # Dersom knappen er trykt bekreftes ny syklustid:
            print("New dutycycle: {} minute/-s".format(dutycycle_input))
            prew_dutycycle_confirm_count = button_clicks                    # Tellevariabel oppdateres
            controller.set_dutycycle(dutycycle_input)                       # Syklustid skrives til regulatoren
            return False                                                    # Bekreftelsesknapp skjules etter bekreftelse
        if (dutycycle_input == controller.get_dutycycle()):                 # Kontrollerer om syklustiden er forandret
            return False                                                    # Bekreftelsesknapp vises ikke dersom regulatorens syklustid stemmer med input-verdien
        else:
            return True                                                     # Bekreftelsesknapp vises dersom syklustiden er forskjellig fra input-verdien

    # Oppdatering av manuelt pådrag fra input
    @app.callback(
        Output(component_id='actuation-confirm-button-collapse', component_property='is_open'),
        [
            Input(component_id='actuation-input', component_property='value'),
            Input(component_id='actuation-confirm-button', component_property='n_clicks'),
        ],
        [
            State(component_id='controller-mode-radioitems', component_property='value'),
            State(component_id='url', component_property='pathname'),
        ]
    )
    def display_manual_actuation_confirm(actuation_input, button_clicks, controller_mode, pathname):
        if (controller_mode == 'Auto'):                                             # Kontrollerer regulatormodusen
            return False                                                            # Skjuler knapp dersom regulatoren står i auto-modus
        else:
            global prew_actuation_confirm_count                                     # Definerer global tellevariabel
            chosen_sløyfe = get_sløyfe_from_pathname(pathname)                      # Bestemmer valgt sløyfe ut ifra pathname
            try:
                controller = get_controller(chosen_sløyfe)                              # Velger regulator avhengig av valgt sløyfe
            except:
                raise PreventUpdate                                                   
            if (button_clicks == None):                                             # button_clicks er None etter at siden lastes inn på nytt
                prew_actuation_confirm_count = 0                                    # Resetter tellevariabelen
            elif (button_clicks > prew_actuation_confirm_count):                    # Dersom knappen er trykt bekreftes nytt manuelt pådrag:
                print("New manual actuation level: {} %".format(actuation_input))
                prew_actuation_confirm_count = button_clicks                        # Tellevariabel oppdateres
                controller.set_u_tot(actuation_input)                               # Manuelt pådrag skrives til regulatoren
                return False                                                        # Bekreftelsesknapp skjules etter bekreftelse
            if (actuation_input == controller.get_u_tot()):                         # Kontrollerer om manuelt er forandret
                return False                                                        # Bekreftelsesknapp vises ikke dersom regulatorens Ti stemmer med input-verdien
            else:
                return True                                                         # Bekreftelsesknapp vises dersom Ti er forskjellig fra input-verdien

    # Aktivering/deaktivering av automatisk av/på-styring
    @app.callback(
        [
            Output(component_id='manual-actuation-radioitems', component_property='options'),
            Output(component_id='manual-actuation-radioitems', component_property='value'),
        ],
        [
            Input(component_id='auto-actuation-checklist', component_property='value'),
        ],
        [
            State(component_id='url', component_property='pathname'),
        ]
    )
    def enable_disable_manual_actuation(auto_actuation, pathname):
        chosen_sløyfe = get_sløyfe_from_pathname(pathname)              # Bestemmer valgt sløyfe ut ifra pathname
        try:
            controller = get_controller(chosen_sløyfe)                  # Velger regulator avhengig av valgt sløyfe
        except:
            raise PreventUpdate                  
        outputState = get_output_state(chosen_sløyfe)[0]                # Henter inn siste loggede relétilstand
        if auto_actuation:                                              # Kontrollerer om automatisk av/på-styring er aktivert
            print("Starting automatic on/off-controlling.")
            controller.start()                                          # Starter automatisk av/på-styring
            return ([
                {'label': "AV", 'value': False, 'disabled': True},
                {'label': "PÅ", 'value': True, 'disabled': True}
            ], not outputState)                                         # Deaktiverer mulighet for manuell styring og oppdaterer utgangsverdi
        else:
            controller.stop()                                           # Stopper automatick av/på-styring
            print("Stoping automatic on/off-controlling.")
            return ([
                {'label': "AV", 'value': False, 'disabled': False},
                {'label': "PÅ", 'value': True, 'disabled': False}
            ], not outputState)                                         # Aktiverer mulighet for manuell styring og oppdaterer utgangsverdi
        
    # Manuell av/på-styring
    @app.callback(
        Output(component_id='manual-actuation-dummy', component_property='children'),
        [
            Input(component_id='manual-actuation-radioitems', component_property='value'),
        ],
        [
            State(component_id='auto-actuation-checklist', component_property='value'),
            State(component_id='url', component_property='pathname'),
        ]
    )
    def activate_deactivate_heat_trace(on_off, auto, pathname):
        chosen_sløyfe = get_sløyfe_from_pathname(pathname)
        outputState = get_output_state(chosen_sløyfe)[0]
        if ((on_off == None) or (auto == None)):
            return "Oppdaterer..."
        if (on_off and not auto and outputState):
            print("Aktiverer varmekabel")
            return activateHeatTrace(chosen_sløyfe)
        elif (not on_off and not auto and not outputState):
            print("Deaktiverer varmekabel")
            return deactivateHeatTrace(chosen_sløyfe)
        else:
            return "Siden er oppdatert"

    # Regulatormodus
    @app.callback(
        Output(component_id='actuation-input', component_property='disabled'),
        [
            Input(component_id='controller-mode-radioitems', component_property='value'),
        ],
        [
            State(component_id='actuation-input', component_property='value'),
            State(component_id='url', component_property='pathname'),
        ]
    )
    def enable_disable_actuation_input(mode, actuation_input, pathname):
        chosen_sløyfe = get_sløyfe_from_pathname(pathname)
        try:
            controller = get_controller(chosen_sløyfe)
        except:
            raise PreventUpdate
        print("Innkommende modus: {}".format(mode))
        if (mode != controller.mode):
            controller.change_mode(mode, actuation_input)
        if (mode == 'Auto'):
            return True
        else:
            return False

    # Oppdater pådraget i input-en til manuelt pådrag, når regulatoren er i auto-modus. (Sikrer rykkfri overgang)
    @app.callback(
        Output(component_id='actuation-input', component_property='value'),
        [
            Input(component_id='interval-component', component_property='n_intervals')
        ],
        [
            State(component_id='url', component_property='pathname'),
        ]
    )
    def update_manual_actuation_in_background(n_intervals, pathname):
        chosen_sløyfe = get_sløyfe_from_pathname(pathname)
        try:
            controller = get_controller(chosen_sløyfe)
        except:
            raise PreventUpdate
        if (controller.mode == 'Auto'):
            return controller.get_u_tot()
        else:
            return no_update