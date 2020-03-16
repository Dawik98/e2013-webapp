

from flask import Flask
from flask_mqtt import Mqtt
import dash


def createServer():

    server = Flask(__name__)

    server.config['SECRET_KEY']='019a82e56daaa961957770fc73e383e4'

    # setup mqtt for mosquitto on vm
    server.config['MQTT_BROKER_URL'] = '13.74.42.218'
    server.config['MQTT_BROKER_PORT'] = 9990
    server.config['MQTT_CLIENT_ID'] = 'Webb-App'
    server.config['MQTT_USERNAME'] = 'e2013'
    server.config['MQTT_PASSWORD'] = 'potet'
    server.config['MQTT_REFRESH_TIME'] = 1.0  # refresh time in seconds

    #mqtt = Mqtt(app_bp)


    from test1 import layout as layout1
    from test1 import callbacks as callbacks1
    addDashApp(server, '/test1/', 'test1', layout1, callbacks1)

    from test2 import layout as layout2
    from test2 import callbacks as callbacks2
    addDashApp(server, '/test2/', 'test2', layout2, callbacks2)

    from flaskApp import app
    server.register_blueprint(app)

    return server


def addDashApp(server, path, title, layout, callbacks):

    dashApp = dash.Dash(__name__, server=server, url_base_pathname=path)

    
    with server.app_context():
        dashApp.title = title
        dashApp.layout = layout
        callbacks(dashApp)



if __name__ == '__main__':
    server = createServer()

    server.run(debug=True)