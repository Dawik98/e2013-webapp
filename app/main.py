from flask import Flask, render_template, request, g, url_for, flash, redirect
from flask_mqtt import Mqtt
from forms import RegistrationForm, LoginForm

import sqlite3
import json
import os
import io

import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.errors as errors
import azure.cosmos.http_constants as http_constants
import azure.cosmos.documents as documents
from decoder import decoder

app = Flask(__name__)

app.config['SECRET_KEY']='019a82e56daaa961957770fc73e383e4'

# collection link in cosmosDB
database_link = 'dbs/E2013'
collection_link='dbs/E2013/colls/'

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




# run when connection with the broker
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe('measurement')
    print("Subscribed to topic")

# run when new message is published to the subscribed topic
@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    topic = message.topic
    payload = json.loads(message.payload.decode()) # get payload and convert it to a dictionary

    print("\nNew message recieved at topic " + topic + ":\n")
    packetData = decoder(payload)
    print(packetData)
    print("\n")

    #write data to database
    container_name = packetData['devicePlacement']
    cosmos = connect_to_db()
    print("Connected to database")

    # create container if it doesn't exist
    try:
        container_definition = {'id': container_name, 'partitionKey': {'paths': ['/'+container_name], 'kind': documents.PartitionKind.Hash}}
        cosmos.CreateContainer(database_link, container_definition, options={'indexingMode': 'none'})
        print("Created container")    
    except errors.HTTPFailure as e:
        if e.status_code == http_constants.StatusCodes.CONFLICT:
            pass
        else:
            raise e


    cosmos.CreateItem(collection_link + container_name, packetData)
    print("Created new Item")

@app.route('/claimMeterdata')
def claimMeterdata():
    print("Sending meterdata-request")
    mqtt.publish('powerSwitch', bytes([4, 2, 0]))
    return "Requesting data"

@app.route('/activateHeatTrace')
def activateHeatTrace():
    print("Sending acivation message")
    mqtt.publish('powerSwitch', bytes([4, 0, 0, 0, 0, 0, 1, 0, 0, 0]))
    return "Sending activation message"

@app.route('/deactivateHeatTrace')
def deactivateHeatTrace():
    print("Sending deactivation message")
    mqtt.publish('powerSwitch', bytes([4, 0, 1, 0, 0, 0, 0, 0, 0, 0]))
    return "Sending deactivation message"

# return containers from cosmos db
#def get_containers():
#    list_of_containers = []
#
#    for i in devices:
#        container = devices[i][0]
#        # add container to list if it isn't added alleready
#        if container in list_of_containers:
#            pass
#        else:
#            list_of_containers.append(container)

#    return list_of_containers

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

    # print(get_containers()) 

    #query data from database
    query = "SELECT * FROM heatTrace1 WHERE heatTrace1.deviceType = 'tempSensor' ORDER BY heatTrace1.timeReceived DESC"

    cosmos = connect_to_db()
    items = cosmos.QueryItems(collection_link+'heatTrace1', query, {'enableCrossPartitionQuery':True})
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
    app.run()
