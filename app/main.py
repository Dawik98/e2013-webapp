from flask import Flask, render_template, request, g, url_for, flash, redirect
from flask_mqtt import Mqtt
from forms import RegistrationForm, LoginForm

import sqlite3
import json
import os

import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.errors as errors
import azure.cosmos.http_constants as http_constants


app = Flask(__name__)

app.config['SECRET_KEY']='019a82e56daaa961957770fc73e383e4'

# collection link in cosmosDB
database_link = 'dbs/E2013'
collection_link='dbs/E2013/colls/heatTrace1'

devices = {'70-b3-d5-80-a0-10-94-3a' : ['varmekabel_1', 'temperature']}

def connect_to_db():
    # setup cosmosDB
    endpoint = 'https://e2013-db.documents.azure.com:443/'
    key = '2bpbyU4kJfh4vgvis2GbDDOpYJmUOfrMTSaXZz4tSas0zPhVvnoLRGSlX5nwFmveFN2iIb1FUudq8kZPpBYDhw=='
    return cosmos_client.CosmosClient(endpoint, {'masterKey': key})


# setup mqtt for mosquitto on vm
app.config['MQTT_BROKER_URL'] = '13.74.42.218'
app.config['MQTT_BROKER_PORT'] = 9990
app.config['MQTT_CLIENT_ID'] = 'Webb-App'
app.config['MQTT_USERNAME'] = 'e2013'
app.config['MQTT_PASSWORD'] = 'potet'
app.config['MQTT_REFRESH_TIME'] = 1.0  # refresh time in seconds
mqtt = Mqtt(app)

#setup mqtt to send to iot-hub
#app.config['MQTT_BROKER_URL'] = 'Bachelorgruppe-E2013.azure-devices.net'
#app.config['MQTT_BROKER_PORT'] = 8883
#app.config['MQTT_CLIENT_ID'] = 'Webb-App'
#app.config['MQTT_USERNAME'] = ''
#app.config['MQTT_PASSWORD'] = ''
#app.config['MQTT_REFRESH_TIME'] = 1.0  # refresh time in seconds
#mqtt = Mqtt(app)


# run when connection with the broker
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe('messurments/#')
    print("Subscribed to topic")

# run when new message is published to the subscribed topic
@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    topic = message.topic
    data = json.loads(message.payload.decode()) # get payload and convert it to a dictionary
    
    print("New message recieved at topic " + topic + " :")
    print(data)

    device_eui = data['device_eui']
    device_placement = devices[device_eui][0]
    device_type = devices[device_eui][1]
        
    # add device data to database
    data['device_placement'] = device_placement
    data['device_type'] = device_type

    #write data to database
    cosmos = connect_to_db()
    print("Creating new container")
    cosmos.CreateContainer(database_link, {'id' : device_placement})
    print("Uploading data to database")    
    cosmos.CreateItem(collection_link, data)

    # send response to node-red
    print("Sending response to node red")
    mqtt.publish('response', 'Message recieved')



# main web page
målinger=[
    {
        'Enhet': 'Temperatur sensor 1',
        'Temperatur': '31',
        'Batteritilstand':'93.7%',
        'Tidspunkt':'12:32:27'
    },
    {
        'Enhet': 'Temperatur sensor 2',
        'Temperatur': '30',
        'Batteritilstand':'92.7%',
        'Tidspunkt':'12:32:29'
    }
]


@app.route('/')
@app.route('/Home')
def Home():

    #query data from database
    query = "SELECT * FROM heatTrace1 WHERE heatTrace1.deviceType = 'tempSensor' ORDER BY heatTrace1._ts DESC"
    cosmos = connect_to_db()
    items = cosmos.QueryItems(collection_link, query, {'enableCrossPartitionQuery':True})
    items = list(items) # save result as list
    print(items)
    val = items[0]['temperature']

    return render_template('index.html',målinger=målinger, val=val)

@app.route('/SensorData')
def about():
    return render_template('SensorData.html', title='Målinger')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('Home'))
    return render_template('register.html', title="Register", form=form)

@app.route('/login')
def login():
    form = LoginForm()
    return render_template('login.html', title="Login", form=form)



if __name__ == '__main__':
    app.run(debug=True)
