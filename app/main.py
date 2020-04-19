from flask import Flask
from flask_mqtt import Mqtt
import dash
import flask_login
import dash_bootstrap_components as dbc
import logging
from getUsers import get_users
from models import User, login_manager
import sys


sys.path.append("./dashApps")



users=get_users()

def createServer():
    server = Flask(__name__)
    server.config['SECRET_KEY']='019a82e56daaa961957770fc73e383e4'

    #_Initialiserer login manager
    login_manager.init_app(server)
    login_manager.login_view='app.login'

    # setup mqtt for mosquitto on vm
    server.config['MQTT_BROKER_URL'] = '13.74.42.218'
    server.config['MQTT_BROKER_PORT'] = 9990
    server.config['MQTT_CLIENT_ID'] = 'Webb-App'
    server.config['MQTT_USERNAME'] = 'e2013'
    server.config['MQTT_PASSWORD'] = 'potet'
    server.config['MQTT_CLIENT_ID'] = "Webb-App"
    server.config['MQTT_REFRESH_TIME'] = 1.0  # refresh time in seconds

    # Koble til Mosquitto
    from mqttCommunication import connect_mosquitto
    connect_mosquitto(server)


    # legg til dashboard apper
    from dashApps.home import layout as layout_home
    from dashApps.home import callbacks as callbacks_home
    addDashApp(server, '/', 'Home', layout_home, callbacks_home)

    from dashApps.sloyfer import layout as layout_sloyfer
    from dashApps.sloyfer import callbacks as callbacks_sloyfer
    addDashApp(server, '/sløyfer/', 'Sløyfer', layout_sloyfer, callbacks_sloyfer)
    
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
def _protect_dashviews(dashapp):
    for view_func in dashapp.server.view_functions:
        if view_func.startswith(dashapp.config.url_base_pathname):
            dashapp.server.view_functions[view_func] = flask_login.login_required(dashapp.server.view_functions[view_func])

def addDashApp(server, path, title, layout, callbacks):

    #external_stylesheets = [{
    #    "href" : "https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css",
    #    "rel" : "stylesheet",
    #    "integrity" : "sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh",
    #    "crossorigin" : "anonymous"
    #    
    #}]
    font_awesome_stylesheets = [{
        "href" : "https://kit.fontawesome.com/274a562a3f.js",
        "crossorigin" : "anonymous"
        
    }]

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
                        #external_stylesheets=external_stylesheets)
                        external_stylesheets=[dbc.themes.SANDSTONE, font_awesome_stylesheets],
                        suppress_callback_exceptions=True)
                        

    
    with server.app_context():
        dashApp.title = title
        dashApp.layout = layout
        callbacks(dashApp)
    
    _protect_dashviews(dashApp)

if __name__ == '__main__':

    server = createServer()
    server.run(host="0.0.0.0", port=8000)
