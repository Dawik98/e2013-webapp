from flask import Flask, render_template, request, g
from flask_mqtt import Mqtt

import sqlite3
import json
import os
import io

import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.errors as errors
import azure.cosmos.http_constants as http_constants
import azure.cosmos.documents as documents


app = Flask(__name__)

# links in cosmosDB
database_link = 'dbs/E2013'
collection_link='dbs/E2013/colls/'

devices = {
    '70-b3-d5-80-a0-10-94-3a' : ['varmekabel_1', 'temperature'],
    '70-b3-d5-80-a0-10-94-46' : ['varmekabel_1', 'temperature'],
    '70-b3-d5-8f-f1-00-1e-78' : ['varmekabel_1', 'power_switch'],
    '70-b3-d5-8f-f1-00-1e-69' : ['varmekabel_2', 'power_switch'],
    
    }

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
    mqtt.subscribe('varmekabel_1')
    print("Subscribed to topic")

# run when new message is published to the subscribed topic
@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    topic = message.topic
    data = json.loads(message.payload.decode()) # get payload and convert it to a dictionary
    #data = message.payload

    print("\nNew message recieved at topic " + topic + " :")
    print(data)
    print(type(data))

    device_eui = data['device_eui']
    device_placement = devices[device_eui][0]
    device_type = devices[device_eui][1]
        
    # add device data to database
    data['device_placement'] = device_placement
    data['device_type'] = device_type

    print(devices)

    #write data to database
    container_name = device_placement
    cosmos = connect_to_db()
    print("Connected to databse")

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


    cosmos.CreateItem(collection_link + container_name, data)
    print("Created new Item")

    # send response to node-red
    print("Sending response to node red")
    mqtt.publish('response', 'Message recieved')

# return containers from cosmos db
def get_containers():
    list_of_containers = []

    for i in devices:
        container = devices[i][0]
        # add container to list if it isn't added alleready
        if container in list_of_containers:
            pass
        else:
            list_of_containers.append(container)

    return list_of_containers

# main web page
@app.route('/')
def hello_world():

    # print(get_containers()) 

    #query data from database
    query = "SELECT * FROM varmekabel_1 WHERE varmekabel_1.device_type = 'temperature' ORDER BY varmekabel_1.time DESC"

    cosmos = connect_to_db()
    items = cosmos.QueryItems(collection_link+'varmekabel_1', query, {'enableCrossPartitionQuery':True})
    items = list(items) # save result as list
    val = items[0]['temperature']

    return render_template('index.html', val=val)


if __name__ == '__main__':
    app.run()
