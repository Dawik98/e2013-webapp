"""
layout.py inneholder:
    - layout somm lastes inn på alle sider
    - funksjoner for å oppdatere alementer utfra valgt sløyfe
"""

import dash
import dash_core_components as dcc 
import dash_html_components as html 
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate


import dash_bootstrap_components as dbc

import json
from itertools import zip_longest

def make_remove_sløyfe_buttons():
    """
    make_remove_sløyfe_buttons lager 20 slettknapper med hver sin unik ID som skal brukes til å kunne slette sløyfer. 
    Grunnen til at alle må defineres på forhånd er at alle id-er/html elementer må eksistere når nettsiden startes for at callback skal kunne kjøres.
    Det kan derfor være nødvendig å definere flere  kanpper hvis sløfen skal ha mer enn 20 enheter

    Returns
    -------
    dict
        remove_buttons_ids innehloder id-er til alle knapper som 'keys' og hvilken enhet de er tilknyttet (eui) som 'value', None i utgangspunktet

    dict
        remove_buttons innehloder id-er til alle knapper som 'keys' og selve knappen i html som 'value'
    """
    remove_buttons_ids = {}
    remove_buttons = {}

    for i in range(20):
        id_ = "delete-sløyfe-{}".format(i+1)
        remove_buttons_ids[id_] = None
        remove_buttons[id_] = html.I(className="fas fa-window-close fa-pull-right fa-lg ", style={'padding-top':'0.9em'}, id=id_)
    
    return remove_buttons_ids, remove_buttons

remove_buttons_ids, remove_buttons = make_remove_sløyfe_buttons()
    
def add_sløyfe_button():
    """
    add_sløyfe_button lager en knapp som vises i dropdown menyen for å legge til en sløyfe

    Returns
    -------
    dash_bootstrap_components
        dbc.Collapse som inneholder dbc.Button
    """

    button = dbc.DropdownMenuItem("Legg til ny sløyfe", id="add-sløyfe-button", toggle=False)
    button_collapse = dbc.Collapse(button, id='add-sløyfe-button-collapse', is_open=True, className="collapsing-no-slide-animation")
    return button_collapse

def add_sløyfe_input():
    """
    add_sløyfe_input er input felte hvor man skriver inn navnet på den nye sløyfen

    Returns
    -------
    dash_bootstrap_components
        dbc.Collapse som inneholder dbc.Input
    """

    sløyfe_input = dbc.DropdownMenuItem(dbc.Input(placeholder="Sløyfe navn", id="add-sløyfe-input"), toggle=False)
    input_collapse = dbc.Collapse(sløyfe_input, id = 'sløyfe-input-collapse', is_open=False)
    return input_collapse

def confirm_buttons():
    """
    confirm_buttons inneholder to knapper som brukes for å godkjenne eller avbryte "adding" av ny sløyfe

    Returns
    -------
    dash_bootstrap_components
        dbc.Collapse som inneholder de to knappene
    """

    button_confirm = dbc.Button("Legg til", id="confirm-add-sløyfe-button", color='success', className='mr-2')
    button_cancel = dbc.Button("Avbryt", id="cancel-add-sløyfe-button", color='danger', className='mr-2')
    button_collapse = dbc.Collapse(dbc.DropdownMenuItem([button_confirm, button_cancel], toggle=False), id='confirm-add-sløyfe-button-collapse', is_open=False, className="collapsing-no-slide-animation")
    return button_collapse

def choose_sløyfe_dropdown(main_url, chosen_sløyfe):
    """
    choose_sløyfe_dropdown lager en dropdown menu hvor man kna velge de forskjellige sløyfene og legge til nye sløyfer

    Parameters
    ----------
    main_url : string
        delen av url som sier hvilken side bruker er på 

    chosen_sløyfe : string
        sløyfe som ble valgt

    Returns
    -------
    dash_bootstrap_components
        dbc.Dropdown
    """
    from dashApps.innstillinger import get_sløyfer
    sløyfer = get_sløyfer() 
    items = []
    for sløyfe, (key, status) in zip_longest(sløyfer, remove_buttons_ids.items()):
        if sløyfe:
            # hver knapp i dropdown menuen er en lenke som sender bruker til /ønsket_side/valgt_sløyfe/ 
            href = "/{}/{}/".format(main_url, sløyfe)
            nav_link = dbc.NavLink(sløyfe, href=href, external_link=True, className='dropdown-item', style={'width':'80%', 'display':'inline-block'})

            delete_button = remove_buttons[key]
            remove_buttons_ids[key]=sløyfe

            items.append(dbc.DropdownMenuItem([nav_link, delete_button], id=sløyfe ))
        elif sløyfe == None:
            # skjul alle slett knappene som ikke er tilskrevet en sløyfe
            delete_button = remove_buttons[key]
            items.append(dbc.DropdownMenuItem(delete_button, style={'display':'none'}))

    # legg til alle elementer i dropdown menu
    items.append(dbc.DropdownMenuItem(divider=True))
    items.append(add_sløyfe_button())
    items.append(add_sløyfe_input())
    items.append(confirm_buttons())

    # oppdater label på dropdown menuen avhengig av hvilken sløfe som er valgt
    label = chosen_sløyfe
    if label == "":
        label = "Velg sløyfe"

    dropdown = dbc.DropdownMenu(label = label, children=items)
    return dropdown

def get_logout_button():
    """
    get_logout_button lager en knapp som brukes til å logge ut av nettsiden
    """
    button = dbc.Button("Logg ut", href='/logout', external_link=True, id='logout-nav-link', color='danger', className='ml-3')
    return button

def get_navbar_items(chosen_sløyfe):
    """
    get_navbar_items lager en navigasjonslenker som brukes til å gå til forskjellige sider

    Parameters
    ----------
    chosen_sløyfe : string
        navn på sløyfen som er valgt

    Returns
    -------
    dash_bootstrap_components
        dbc.Nav
    """

    navbar_items = [
        dbc.NavLink("Hjem", href="/hjem/{}".format(chosen_sløyfe), external_link=True),
        dbc.NavLink("Trend", href="/trend/{}".format(chosen_sløyfe), external_link=True, id='sløyfe-nav-link'),
        dbc.NavLink("Historikk", href="/historikk/{}".format(chosen_sløyfe), external_link=True, id='sløyfe-nav-link'),
        dbc.NavLink("Alarmer", href="/alarmer/{}".format(chosen_sløyfe), external_link=True, id='alarmer-nav-link'),
        dbc.NavLink("Innstillinger", href="/innstillinger/{}".format(chosen_sløyfe), external_link=True, id='innstillinger-nav-link'),
        ]

    return dbc.Nav(navbar_items, className="mr-auto", navbar=True,)


# header er navigasjonsraden som ligger øverst på siden og brukes til å navigere i webappen
header = html.Div([dcc.Location(id='url', refresh=False), dcc.Location(id='update-url', refresh=True), 
    dbc.Navbar(dbc.Container(
        [
            dbc.NavbarBrand("E2013", href="/", external_link=True),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                id="navbar-collapse",
                navbar=True,
            ),
            html.Div(choose_sløyfe_dropdown('', ''), id='choose-sløyfe'), # kjører choose_sløfe_dropdaown for at callbacks akal ha tilllgang til alle elementer
            html.Div(get_logout_button()),
        ]),
    className="mb-5",
    color="primary",
    dark=True,
    sticky="top"
)])

def callbacks(app):
    # add callback for toggling the collapse on small screens
    @app.callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")],
    )
    def toggle_navbar_collapse(n, is_open):
        if n:
            return not is_open
        return is_open

    # oppdaterer navigasjonsbaren når ny sløyfe blir valgt eller nå bruker går til ny side
    @app.callback(
        Output(component_id='navbar-collapse', component_property='children'),
        [Input(component_id='url', component_property='pathname')])
    def update_navbar_by_sløyfe(pathname):

        main_url = pathname.split('/')[1]
        try:
            chosen_sløyfe = pathname.split('/')[2]
        except:
            chosen_sløyfe = ""

        return get_navbar_items(chosen_sløyfe)

    # lager alle sletknappene som brukes til å slette sløyfer
    def delete_buttons_inputs():
        inputs = []

        for key, status in remove_buttons_ids.items():
            inputs.append(Input(component_id=key, component_property='n_clicks'))
        return inputs

    # oppdater sløyfe dropdown menu når det legges til / slettes en sløyfe eller det velges en sløyfe
    @app.callback(
        Output('choose-sløyfe', 'children'),
        [Input('url', 'pathname'),
        Input('confirm-add-sløyfe-button', 'n_clicks')] + delete_buttons_inputs(),
        [State('url', 'pathname'),
        State('add-sløyfe-input', 'value')])
    def update_choose_sløyfe_dropdown(pathname_input, *args):
        from dashApps.innstillinger import add_sløyfe, remove_sløyfe
        #print("running update_choose_sløyfe_dropdown")

        ctx = dash.callback_context
        try: 
            triggered_by = ctx.triggered[0]['prop_id'].split('.')[0]
        except:
            pass

        states = ctx.states
        inputs = ctx.inputs

        pathname_state = states['url.pathname']
        new_sløyfe_name = states['add-sløyfe-input.value']

        def split_url(pathname):
            main_url = pathname.split('/')[1]
            try:
                chosen_sløyfe = pathname.split('/')[2]
            except:
                chosen_sløyfe = ""
            return main_url, chosen_sløyfe

        if triggered_by == 'url':
            # url vil forandres når ny sløyfe blir valgt
            main_url, chosen_sløyfe = split_url(pathname_input)
            return choose_sløyfe_dropdown(main_url, chosen_sløyfe)
        elif triggered_by == 'confirm-add-sløyfe-button' and (new_sløyfe_name != None or new_sløyfe_name == ""):
            # hvis det lelgges til ny sløyfe
            main_url, chosen_sløyfe = split_url(pathname_state)
            print("Adding sløyfe {}".format(new_sløyfe_name))
            add_sløyfe(new_sløyfe_name)
            return choose_sløyfe_dropdown(main_url, chosen_sløyfe)
        elif 'delete' in triggered_by:
            # hvis en sløyfe blir slettet
            from mqttCommunication import deleteController
            main_url, chosen_sløyfe = split_url(pathname_state)
            sløyfe = remove_buttons_ids[triggered_by]
            print("Removing sløyfe {}".format(sløyfe))
            remove_sløyfe(sløyfe)
            try:
                # Hvis det er en regulator i sløyfe slett den 
                deleteController(sløyfe)
            except KeyError:
                print('Deleting controller... Controller does not exsist')
            return choose_sløyfe_dropdown(main_url, chosen_sløyfe)
        else:
            print("Prevent update")
            raise PreventUpdate

    @app.callback(
        Output('update-url', 'pathname'),
        delete_buttons_inputs(),
        [State('url', 'pathname')]
    )
    def update_url(*args): 
    # Hvis en sløyfe som er åpen slettes send bruker til hjem-siden
        from dashApps.innstillinger import get_sløyfer
        from time import sleep
        sleep(0.2)

        ctx = dash.callback_context
        states = ctx.states
        pathname = states['url.pathname']
        chosen_sløyfe = get_sløyfe_from_pathname(pathname)
        sløyfer = get_sløyfer()

        if chosen_sløyfe in sløyfer or chosen_sløyfe == '':
            raise PreventUpdate
        else:
            return '/hjem/'

    # Vis / skjul input for å leggen inn ny enhet
    @app.callback(
        Output(component_id='sløyfe-input-collapse', component_property='is_open'),
        [Input(component_id='add-sløyfe-button', component_property='n_clicks'),
        Input(component_id='confirm-add-sløyfe-button', component_property='n_clicks'),
        Input(component_id='cancel-add-sløyfe-button', component_property='n_clicks'),],
        [State(component_id='sløyfe-input-collapse', component_property='is_open'),
        ])
    def display_input_row(click_add_device, click_confirm_add, click_cancel_add, is_open):
        if click_add_device or click_cancel_add or click_confirm_add:
            return not is_open
        return False

    # Vis / skjul knapp for å legge til ny enhet
    @app.callback(
        Output(component_id='add-sløyfe-button-collapse', component_property='is_open'),
        [Input(component_id='add-sløyfe-button', component_property='n_clicks'),
        Input(component_id='confirm-add-sløyfe-button', component_property='n_clicks'),
        Input(component_id='cancel-add-sløyfe-button', component_property='n_clicks'),],
        [State(component_id='add-sløyfe-button-collapse', component_property='is_open'),
        State(component_id='confirm-add-sløyfe-button-collapse', component_property='is_open'),
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
        Output(component_id='confirm-add-sløyfe-button-collapse', component_property='is_open'),
        [Input(component_id='add-sløyfe-button', component_property='n_clicks'),
        Input(component_id='confirm-add-sløyfe-button', component_property='n_clicks'),
        Input(component_id='cancel-add-sløyfe-button', component_property='n_clicks'),],
        [State(component_id='add-sløyfe-button-collapse', component_property='is_open'),
        State(component_id='confirm-add-sløyfe-button-collapse', component_property='is_open'),
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
        Output(component_id='add-sløyfe-input', component_property='value'),
        [Input(component_id='cancel-add-sløyfe-button', component_property='n_clicks'),
        Input(component_id='confirm-add-sløyfe-button', component_property='n_clicks'),
        ])
    def display_confirm_buttons(click_cancel_add, click_confirm_add):
        if click_cancel_add or click_confirm_add:
            return ""
    
    @app.callback(
        Output('main-container', 'children'),
        [Input('url', 'pathname')]
    )
    def got_sløyfe(pathname):
        chosen_sløyfe = get_sløyfe_from_pathname(pathname)
        print("chosen sløyfe = '{}'".format(chosen_sløyfe))

        # Hvis ingen sløyfe er valgt be bruker velge en
        if chosen_sløyfe == '':
            notification = html.Div([html.H2(["Velg en sløyfe for å fortsette!", html.I(className="fas fa-arrow-up ml-3")])], className="text-right text-info", style={'margin-right':'10em'})
            return notification
        else:
            raise PreventUpdate


#------------------------------- Sløyfe valg funksjoner -------------------------------

# returnerer siste bit av url addressen = valgt sløyfe
def get_sløyfe_from_pathname(pathname):
    try:
        chosen_sløyfe = pathname.split('/')[2]
    except:
        chosen_sløyfe = "Ingen sløyfe ble valgt"
    return chosen_sløyfe

def update_sløyfe_callback(app, item_list):
    """
    update_sløyfe_callback oppdaterer html elementer som tar valgt sløyfe inn som en argument f.eks. site-title
    legg inn denne funksjonen sammen med andre callbacks på siden hvor den skal brukes 

    Parameters
    ----------
    app : dash.Dash
        dashApp som brukes i valgt side

    item_list : list
        item_list skal inneholde lister med id til html elementer som er avhengig av valgt sløyfe og funksjonen som returnerer det elementet
        hver elemnt i listen skal være en liste: [id, func]...

    """
    
    callback_outputs = []

    # lager output til alle elementer som skal oppdateres
    for item in item_list:
        callback_output = Output(component_id=item[0], component_property='children')
        callback_outputs.append(callback_output)

    @app.callback(callback_outputs, [Input(component_id='url', component_property='pathname')])
    def update_sløyfe(pathname):
        chosen_sløyfe=get_sløyfe_from_pathname(pathname)

        site_components=[]
        for item in item_list:
            # kjører alle funksjoner for å tak i oppdaterte html elementer med 'chosen_sløyfe' som argument
            component = item[1](chosen_sløyfe)
            site_components.append(component)

        # returnerer alle oppddaterte elementer
        return tuple(site_components)
