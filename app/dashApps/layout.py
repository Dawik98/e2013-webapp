1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
83
84
85
86
87
88
89
90
91
92
93
94
95
96
97
98
99
100
101
102
103
104
105
106
107
108
109
110
111
112
113
114
115
116
117
118
119
120
121
122
123
124
125
126
127
128
129
130
131
132
133
import dash
import dash_core_components as dcc 
import dash_html_components as html 
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import json
current_url = ""
#def get_url():
#    url = current_url.split('/')[0]
#    print("url = " + url)
#    return url
#def get_chosen_sløyfe():
#    print(current_url)
#    try: 
#        chosen_sløyfe = current_url.split('/')[2]
#        return chosen_sløyfe
#    except:
#        return "blablabal"
def get_sløyfer():
    sløyfer = []
    with open('app/settings.txt') as json_file:
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
        items.append(dbc.DropdownMenuItem(dbc.NavLink(sløyfe, href=href, external_link=True), id=sløyfe, className='ml'))
    label = chosen_sløyfe
    print("label = " + label)
    if label == "":
        label = "Velg sløyfe"
    dropdown = dbc.DropdownMenu(label = label, children=items)
    return dropdown
def get_navbar_items(chosen_sløyfe):
    navbar_items = [
        dbc.NavLink("Home", href="/Home/", external_link=True),
        dbc.NavLink("Sløyfer", href="/sløyfer/{}".format(chosen_sløyfe), external_link=True, id='sløyfe-nav-link'),
        dbc.NavLink("Historikk", href="/historikk/{}".format(chosen_sløyfe), external_link=True, id='sløyfe-nav-link'),
        dbc.NavLink("Alarmer", href="/alarmer/{}".format(chosen_sløyfe), external_link=True, id='alarmer-nav-link'),
        dbc.NavLink("Innstillinger", href="/instillinger/{}".format(chosen_sløyfe), external_link=True, id='innstillinger-nav-link'),
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