from decoder import decoder
from flask_mqtt import Mqtt
from powerControl import PI_controller

from cosmosDB import connect_to_db, write_to_db
import json, time, datetime, pytz

mqtt = None
packetData = {}
outputState = {}
timeOslo = datetime.time()

def connect_mosquitto(server):
    global mqtt
    mqtt = Mqtt(server)

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
        global timeOslo
        global packetData
        packetData, timeOslo = decoder(payload)
        print(packetData)
        if (packetData['messageType'] == 'ioData'):
            global outputState
            outputState = {
                packetData['devicePlacement']: [packetData['output'], timeOslo]
            }
        elif (packetData['messageType'] == 'dataLog'):
            controller1.update_value(packetData['temperature'])
            
        #write data to database
        container_name = packetData['devicePlacement']
    
        write_to_db(container_name, packetData)
    
def claimMeterdata(devicePlacement):
    startTime = datetime.datetime.now().astimezone(pytz.timezone('Europe/Oslo'))
    attempts = 0
    while (((packetData['messageType'] != 'powerData') or (packetData['devicePlacement'] != devicePlacement) or (timeOslo < startTime)) and (attempts < 5)):
        mqtt.publish('powerSwitch', bytes([4, 2, 0]))
        attempts += 1
        print("Meterdata request were sent. This is the {}. attempt.".format(attempts))
        print("Going to sleep for 5 seconds")
        time.sleep(5)
        print("Woke up from sleep")
    if ((packetData['messageType'] != 'powerData') or (packetData['devicePlacement'] != devicePlacement) or (timeOslo < startTime)):
        return ("Did not receive meterdata response. Message were sent 5 times")
    else:
        return ("Meterdata request has been sent to gateway. Response were received within the {}. attempt.".format(attempts))

def activateHeatTrace(devicePlacement):
    startTime = datetime.datetime.now().astimezone(pytz.timezone('Europe/Oslo'))
    attempts = 0
    while ((outputState[devicePlacement][0] == True) and (attempts < 5)):
        mqtt.publish('powerSwitch', bytes([4, 0, 0, 0, 0, 0, 1, 0, 0, 0]))
        attempts += 1
        print("Activation message has been sent. This is the {}. attempt.".format(attempts))
        print("Going to sleep for 5 seconds.")
        time.sleep(5)
        print("Woke up from sleep.")
    if (outputState[devicePlacement][1] < startTime):
        return ("Heat Trace are already activated")
    elif (outputState[devicePlacement][0] == True):
        return ("Did not receive confirmation of activation. Message were sent 5 times.")
    else:
        return ("Activation message has been sent to gateway. Confirmation were received within the {}. attempt.".format(attempts))

def deactivateHeatTrace(devicePlacement):
    startTime = datetime.datetime.now().astimezone(pytz.timezone('Europe/Oslo'))
    attempts = 0
    while ((outputState[devicePlacement][0] == False) and (attempts < 5)):
        mqtt.publish('powerSwitch', bytes([4, 0, 1, 0, 0, 0, 0, 0, 0, 0]))
        attempts += 1
        print("Deactivation message has been sent. This is the {}. attempt.".format(attempts))
        print("Going to sleep for 5 seconds.")
        time.sleep(5)
        print("Woke up from sleep.")
    if (outputState[devicePlacement][1] < startTime):
        return ("Heat Trace are already deactivated")
    elif (outputState[devicePlacement][0] == False):
        return ("Did not receive confirmation of deactivation. Message were sent 5 times.")
    else:
        return ("Deactivation message has been sent to gateway. Confirmation were received within the {}. attempt.".format(attempts))

controller1 = PI_controller('heatTrace1', activateHeatTrace, deactivateHeatTrace)
# controller1.set_dutycycle(10.0/60)
controller1.update_parameters(1.0, 1.0)
controller1.update_setpoint(60.0)