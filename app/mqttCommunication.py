from decoder import decoder
from flask_mqtt import Mqtt
from powerControl import PI_controller

from cosmosDB import connect_to_db, write_to_db
import json, time, datetime, pytz

mqtt = None
packetData = {}
# Initialiserer utgangstilstand i tilfelle strømbrudd
outputState = {
    'heatTrace1': [False, datetime.datetime.now().astimezone(pytz.timezone('Europe/Oslo'))]
}
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
        # print(payload)
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

# Utsending av "Meter-data-request"
def claimMeterdata(devicePlacement):
    startTime = datetime.datetime.now().astimezone(pytz.timezone('Europe/Oslo')) # Definerer starttidspunkt med tidssonestempel +01.00
    attempts = 0 # Initialiserer en forsøks-teller
    # Kjør while-løkke så lenge siste pakketype er ulik "powerData" || eller pakken tilhører en annen heat trace sløyfe || eller siste mottatte pakke er eldre enn
    # starttidspunktet til denne løkken || og det er gjennomført inntil 5 forsøk.
    while (((packetData['messageType'] != 'powerData') or (packetData['devicePlacement'] != devicePlacement) or (timeOslo < startTime)) and (attempts < 5)):
        mqtt.publish('powerSwitch', bytes([4, 2, 0])) # Pakke sendes til Mosquitto MQTT Broker, videre til Node-Red og til slutt til målereléet.
        attempts += 1 # Øker verdien til forsøkstelleren.
        print("Meterdata request were sent. This is the {}. attempt.".format(attempts))
        print("Going to sleep for 5 seconds")
        time.sleep(5) # Løkken sover i 5 sekunder for å vente på pakketransport.
        print("Woke up from sleep")
    # Dersom det ikke kom inn noen ny eller riktig pakke etter 5 forsøk returneres det en feilmelding.
    if ((packetData['messageType'] != 'powerData') or (packetData['devicePlacement'] != devicePlacement) or (timeOslo < startTime)):
        return ("Did not receive meterdata response. Message were sent 5 times")
    # Dersom riktig pakke ble mottatt returneres respons med informasjon om antall forsøk som ble benyttet.
    else:
        return ("Meterdata request has been sent to gateway. Response were received within the {}. attempt.".format(attempts))

# Aktivering av varmekabel der sløyfevariabelen er argumentet (heatTrace1, heatTrace2, osv...)
def activateHeatTrace(devicePlacement):
    startTime = datetime.datetime.now().astimezone(pytz.timezone('Europe/Oslo')) # Definerer starttidspunkt med tidssonestempel +01.00
    attempts = 0 # Initialiserer en forsøks-teller
    # Kjør while-løkken dersom den aktuelle varmekabelen allerede er aktivert. Styringen er koblet NC (normal closed). Dermed er tilstanden TRUE
    # når varmekabelen er av. Løkken stopper dersom antall forsøk overstiges (maks 5 forsøk).
    while ((outputState[devicePlacement][0] == True) and (attempts < 5)):
        mqtt.publish('powerSwitch', bytes([4, 0, 0, 0, 0, 0, 1, 0, 0, 0])) # Pakke sendes til Mosquitto MQTT Broker, videre til Node-Red og til slutt til målereléet.
        attempts += 1 # Øker verdien til forsøkstelleren
        print("Activation message has been sent. This is the {}. attempt.".format(attempts))
        print("Going to sleep for 5 seconds.")
        time.sleep(5) # Løkken sover i 5 sekunder for å vente på pakketransport.
        print("Woke up from sleep.")
    # Dersom aktiveringstidspunktet var før denne funksjonen startet returneres denne beskjeden.
    if (outputState[devicePlacement][1] < startTime):
        return ("Heat Trace are already activated")
    # Dersom utgangstilstanden fortsatt er True fungerte ikke aktiveringen, eller det er ikke mottatt bekreftelse på aktivering.
    elif (outputState[devicePlacement][0] == True):
        return ("Did not receive confirmation of activation. Message were sent 5 times.")
    # I andre tilfeller har aktiveringen lyktes og informasjon med antall forsøk returneres.
    else:
        return ("Activation message has been sent to gateway. Confirmation were received within the {}. attempt.".format(attempts))

# Deaktivering av varmekabel der sløyfevariabelen er argumentet (heatTrace1, heatTrace2, osv...)
def deactivateHeatTrace(devicePlacement):
    startTime = datetime.datetime.now().astimezone(pytz.timezone('Europe/Oslo')) # Definerer starttidspunkt med tidssonestempel +01.00
    attempts = 0 # Initialiserer en forsøks-teller
    # Kjør while-løkken dersom den aktuelle varmekabelen allerede er deaktivert. Styringen er koblet NC (normal closed). Dermed er tilstanden FALSE
    # når varmekabelen er på. Løkken stopper dersom antall forsøk overstiges (maks 5 forsøk).
    while ((outputState[devicePlacement][0] == False) and (attempts < 5)):
        mqtt.publish('powerSwitch', bytes([4, 0, 1, 0, 0, 0, 0, 0, 0, 0])) # Pakke sendes til Mosquitto MQTT Broker, videre til Node-Red og til slutt til målereléet.
        attempts += 1 # Øker verdien til forsøkstelleren
        print("Deactivation message has been sent. This is the {}. attempt.".format(attempts))
        print("Going to sleep for 5 seconds.")
        time.sleep(5) # Løkken sover i 5 sekunder for å vente på pakketransport.
        print("Woke up from sleep.")
    # Dersom deaktiveringstidspunktet var før denne funksjonen startet returneres denne beskjeden.
    if (outputState[devicePlacement][1] < startTime):
        return ("Heat Trace are already deactivated")
    # Dersom utgangstilstanden fortsatt er FALSE fungerte ikke deaktiveringen, eller det er ikke mottatt bekreftelse på deaktivering.
    elif (outputState[devicePlacement][0] == False):
        return ("Did not receive confirmation of deactivation. Message were sent 5 times.")
    # I andre tilfeller har deaktiveringen lyktes og informasjon med antall forsøk returneres.
    else:
        return ("Deactivation message has been sent to gateway. Confirmation were received within the {}. attempt.".format(attempts))

controller1 = PI_controller('heatTrace1', activateHeatTrace, deactivateHeatTrace)
# controller1.set_dutycycle(10.0/60)
#controller1.update_parameters(3.0, 0.0)
#controller1.update_setpoint(20.0)