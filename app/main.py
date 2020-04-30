from flask import Flask
from flask_mqtt import Mqtt
import dash
import flask_login
import dash_bootstrap_components as dbc
import logging

from login import get_users, User, login_manager


import json
import os
import sys
from flask_mail import Mail

sys.path.append("./dashApps")

# Velges avhengig av om appen kjøres lokalt eller i Azure
# usersFile = 'users.txt' # Azure
usersFile = 'app/users.txt' # Lokalt
# baseURL = 'http://e2013-ntnu.azurewebsites.net' # Azure
baseURL = 'http://localhost:8000' # Lokalt

def createServer():
    server = Flask(__name__)
    server.config['SECRET_KEY']='019a82e56daaa961957770fc73e383e4'
    #_Initialiserer login manager
    login_manager.init_app(server)
    login_manager.login_view='app.login'
    users=get_users()

    with open(usersFile, 'r+') as json_file:
        json.dump(users, json_file)

    # legger inn all nødvendig data for mosquitto klient
    server.config['MQTT_BROKER_URL'] = '13.74.42.218'
    server.config['MQTT_BROKER_PORT'] = 9990
    server.config['MQTT_CLIENT_ID'] = 'Webb-App'
    server.config['MQTT_USERNAME'] = 'e2013'
    server.config['MQTT_PASSWORD'] = 'potet'
    server.config['MQTT_CLIENT_ID'] = "Webb-App"
    server.config['MQTT_REFRESH_TIME'] = 1.0  # refresh time in seconds

    # email server
    server.config['MAIL_SERVER'] = 'smtp.gmail.com'
    server.config['MAIL_PORT'] = 465
    server.config['MAIL_USE_TLS'] = False
    server.config['MAIL_USE_SSL'] = True
    server.config['MAIL_DEFAULT_SENDER'] = 'bachelorgrupee2013@gmail.com'

    # Legger brukernavn og passord inn i enviorment variabel. Det er tryggere enn å legge de direkte i source file
    # Endres om vi kjører lokalt eller lastet opp i Azure ##
    # server.config['MAIL_USERNAME'] = 'bachelorgruppee2013@gmail.com' # Lokalt
    # server.config['MAIL_PASSWORD'] = 'E2013LoRa' # Lokalt
    server.config['MAIL_USERNAME'] = os.environ.get('bachelorgruppee2013@gmail.com') # Azure
    server.config['MAIL_PASSWORD'] = os.environ.get('E2013LoRa') # Azure
    
    from login import connect_mail
    connect_mail(server)

    # Koble til Mosquitto
    from mqttCommunication import connect_mosquitto
    connect_mosquitto(server)

    # legg til dashboard apper
    from dashApps.home import layout as layout_home
    from dashApps.home import callbacks as callbacks_home
    addDashApp(server, '/hjem/', 'Hjem', layout_home, callbacks_home)

    from dashApps.sloyfer import layout as layout_sloyfer
    from dashApps.sloyfer import callbacks as callbacks_sloyfer
    addDashApp(server, '/trend/', 'Trend', layout_sloyfer, callbacks_sloyfer)
    
    from dashApps.historikk import layout as layout_historikk
    from dashApps.historikk import callbacks as callbacks_historikk
    addDashApp(server, '/historikk/', 'historikk', layout_historikk, callbacks_historikk)

    from dashApps.alarmer import layout as layout_alarmer
    from dashApps.alarmer import callbacks as callbacks_alarmer
    addDashApp(server, '/alarmer/', 'Alarmer', layout_alarmer, callbacks_alarmer)
    
    from dashApps.innstillinger import layout as layout_innstillinger
    from dashApps.innstillinger import callbacks as callbacks_innstillinger
    addDashApp(server, '/innstillinger/', 'Innstillinger', layout_innstillinger, callbacks_innstillinger)


    from flaskApp import app
    
    server.register_blueprint(app)

    return server

#Funksjon som beskytter dashappene med at vi krever innlognings status.     
def _protect_dashviews(dashapp):
    for view_func in dashapp.server.view_functions:
        if view_func.startswith(dashapp.config.url_base_pathname):
            dashapp.server.view_functions[view_func] = flask_login.login_required(dashapp.server.view_functions[view_func])

# Lager en funksjon for å kunne enkelt legge til flere dash-apps
def addDashApp(server, path, title, layout, callbacks):

    # Inkluderer en font med ikoner
    font_awesome_stylesheets = [{
        "href" : "https://kit.fontawesome.com/274a562a3f.js",
        "crossorigin" : "anonymous"
        
    }]

    # Inkluder nødvendige script bla. for bootstrap
    external_scripts = [{
        "href" : "https://code.jquery.com/jquery-3.4.1.slim.min.js",
        "integrity" : "sha384-J6qa4849blE2+poT4WnyKhv5vZF5SrPo0iEjwBvKU7imGFAV0wwj1yYfoRSJoZ+n",
        "crossorigin" : "anonymous"
        },{
        "href" : "https://cdn.jsdelivr.net/npm/popper.js@1.16.0/dist/umd/popper.min.js",
        "integrity" : "sha384-Q6E9RHvbIyZFJoft+2mJbHaEWldlvI9IOYy5n3zV9zzTtmI3UksdQRVvoxMfooAo",
        "crossorigin" : "anonymous"
        },{
        "href" : "https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/js/bootstrap.min.js",
        "integrity" : "sha384-wfSDF2E50Y2D1uUdj0O3uMBJnjuUD4Ih7YwaYd1iqfktj0Uod8GCExl3Og8ifwB6",
        "crossorigin" : "anonymous"
        }
    ]

    dashApp = dash.Dash(__name__, 
                        server=server,
                        url_base_pathname=path, 
                        external_scripts=external_scripts, 
                        external_stylesheets=[dbc.themes.SANDSTONE, font_awesome_stylesheets],
                        suppress_callback_exceptions=True)
                        
    with server.app_context():
        dashApp.title = title
        dashApp.layout = layout
        callbacks(dashApp)
    
    # Beskytter dashappene (dashboardet) med innloggning
    _protect_dashviews(dashApp)

if __name__ == '__main__':

    server = createServer()
    server.run(host="0.0.0.0", port=8000)
