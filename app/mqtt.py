from decoder import decoder
from flask_mqtt import Mqtt

from cosmosDB import connect_to_db, write_to_db
import json

mqtt = Mqtt()



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

    print("\nNew message recieved at topic " + topic + " :")
    print(payload)
    packetData = decoder(payload)
    print(packetData)

    #write data to database
    container_name = packetData['devicePlacement']

    write_to_db(container_name, packetData)
    

    
    
    
    
    
    
    
    
    
    


    
    