import dash
import dash_core_components as dcc 
import dash_html_components as html 
from dash.dependencies import Input, Output, State

import dash_bootstrap_components as dbc

import json

# Velges avhengig av om appen kjøres lokalt eller i Azure
settingsFile = 'settings.txt' # Azure
# settingsFile = 'app/settings.txt' # Lokalt

current_url = ""

def get_sløyfer():
    sløyfer = []
    with open(settingsFile) as json_file:
        data = json.load(json_file)
        for key, value in data.items():
            sløyfer.append(key)

    return sløyfer

def choose_sløyfe_dropdown(main_url, chosen_sløyfe):
    sløyfer = get_sløyfer() 
    items = []
    for sløyfe in sløyfer:
        href = "/{}/{}/".format(main_url, sløyfe)
        print(href)
        items.append(dbc.DropdownMenuItem(dbc.NavLink(sløyfe, href=href, external_link=True, className='dropdown-item'), id=sløyfe, className='ml'))

    label = chosen_sløyfe
    print("label = " + label)
    if label == "":
        label = "Velg sløyfe"

    dropdown = dbc.DropdownMenu(label = label, children=items)
    return dropdown

def get_navbar_items(chosen_sløyfe):

    navbar_items = [
        dbc.NavLink("Home", href="/Home/{}".format(chosen_sløyfe), external_link=True),
        dbc.NavLink("Sløyfer", href="/sløyfer/{}".format(chosen_sløyfe), external_link=True, id='sløyfe-nav-link'),
        dbc.NavLink("Alarmer", href="/alarmer/{}".format(chosen_sløyfe), external_link=True, id='alarmer-nav-link'),
        dbc.NavLink("Innstillinger", href="/innstillinger/{}".format(chosen_sløyfe), external_link=True, id='innstillinger-nav-link'),
        ]

    return dbc.Nav(navbar_items, className="mr-auto", navbar=True,)


header = html.Div([dcc.Location(id='url', refresh=False), html.Div(id='dummy-label'),
    dbc.Navbar(dbc.Container(
        [
            dbc.NavbarBrand("E2013", href="/Home", external_link=True),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                id="navbar-collapse",
                navbar=True,
            ),
            html.Div(id='choose-sløyfe'),
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

    @app.callback([
        Output(component_id='choose-sløyfe', component_property='children'),
        Output(component_id='navbar-collapse', component_property='children')],
        [
        Input(component_id='url', component_property='pathname'),])
    def update_navbar_by_sløyfe(pathname):
        main_url = pathname.split('/')[1]
        try:
            chosen_sløyfe = pathname.split('/')[2]
        except:
            chosen_sløyfe = ""

        return choose_sløyfe_dropdown(main_url, chosen_sløyfe), get_navbar_items(chosen_sløyfe)
        

# returnerer siste bit av url addressen = valgt sløyfe
def get_sløyfe_from_pathname(pathname):
        try:
            chosen_sløyfe = pathname.split('/')[2]
        except:
            chosen_sløyfe = "Ingen sløyfe ble valgt"
        return chosen_sløyfe

def update_sløyfe_callback(app, item_list):
    # item_list skal inneholde lister med id til items som er avhengig av valgt sløyfe og funksjonen som returnerer den item
    # hver elemnt i listen skal være liste: [id, func]...
    
    callback_outputs = []

    for item in item_list:
        callback_output = Output(component_id=item[0], component_property='children')
        callback_outputs.append(callback_output)

    @app.callback(callback_outputs, [Input(component_id='url', component_property='pathname')])
    def update_sløyfe(pathname):
        chosen_sløyfe=get_sløyfe_from_pathname(pathname)

        site_components=[]
        for item in item_list:
            component = item[1](chosen_sløyfe)
            site_components.append(component)

        return tuple(site_components)
