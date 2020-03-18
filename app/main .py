from flask import Flask
from flask_mqtt import Mqtt
import dash

import sys
sys.path.append("./dashApps")


def createServer():

    server = Flask(__name__)

    server.config['SECRET_KEY']='019a82e56daaa961957770fc73e383e4'

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

    from dashApps.test1 import layout as layout1
    from dashApps.test1 import callbacks as callbacks1
    addDashApp(server, '/test1/', 'test1', layout1, callbacks1)

    from dashApps.test2 import layout as layout2
    from dashApps.test2 import callbacks as callbacks2
    addDashApp(server, '/test2/', 'test2', layout2, callbacks2)

    from dashApps.sloyfer import layout as layout_sloyfer
    from dashApps.sloyfer import callbacks as callbacks_sloyfer
    addDashApp(server, '/sløyfer/', 'sloyfer', layout_sloyfer, callbacks_sloyfer)


    from flaskApp import app
    server.register_blueprint(app)

    return server


def addDashApp(server, path, title, layout, callbacks):

    external_stylesheets = [{
        "href" : "https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css",
        "rel" : "stylesheet",
        "integrity" : "sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh",
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
                        external_stylesheets=external_stylesheets)

    
    with server.app_context():
        dashApp.title = title
        dashApp.layout = layout
        callbacks(dashApp)



if __name__ == '__main__':
    server = createServer()

    server.run(debug=True)