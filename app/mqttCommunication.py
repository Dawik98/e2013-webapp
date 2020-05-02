from decoder import decoder
from flask_mqtt import Mqtt
from powerControl import PI_controller
from cosmosDB import connect_to_db, write_to_db, read_from_db
import json, time, pytz, datetime
from datetime import datetime as dt

# Velges avhengig av om appen kjøres lokalt eller i Azure
gatewayFile = 'gatewayStatus.txt' # Azure
# gatewayFile = 'app/gatewayStatus.txt' # Lokalt

mqtt = None

def connect_mosquitto(server):
    global mqtt
    mqtt = Mqtt(server)

    # run when connection with the broker
    @mqtt.on_connect()
    def handle_connect(client, userdata, flags, rc):
        mqtt.subscribe('measurement')
        print("[MQTT] Subscribed to topic: measurement")
        mqtt.subscribe('gatewayStatus')
        print("[MQTT] Subscribed to topic: gatewayStatus")
    
    # run when new message is published to the subscribed topic
    @mqtt.on_message()
    def handle_mqtt_message(client, userdata, message):
        topic = message.topic
    
        print("\n[MQTT] New message recieved at topic {}:".format(topic))
        if topic == 'measurement':
            payload = json.loads(message.payload.decode()) # get payload and convert it to a dictionary
            # print(payload)

            global timeOslo
            global packetData
            packetData, timeOslo = decoder(payload)
            print(packetData)
            if (packetData['messageType'] == 'ioData'):
                global outputState
                outputState[packetData['devicePlacement']] = [packetData['output'], timeOslo]
                print("outputState: {}".format(outputState[packetData['devicePlacement']][0]))
            elif ((packetData['messageType'] == 'dataLog') and (packetData['devicePlacement'] in controller)):
                from dashApps.innstillinger import get_temp_sensors_in_placement
                devicesInPlacement = get_temp_sensors_in_placement(packetData['devicePlacement'])
                if (len(devicesInPlacement) > 1):
                    query = "SELECT {0}.temperature, {0}.deviceEui FROM {0} WHERE {0}.timeReceived > '{1}' ORDER BY {0}.timeReceived DESC".format(packetData['devicePlacement'], (timeOslo - dt.timedelta(minutes=7)))
                    lastTemps = read_from_db(packetData['devicePlacement'], query)
                    # Fjerner enhets-EUI til avsenderenhet fra listen over enheter i varmekretsen
                    devicesInPlacement.remove(packetData['deviceEui'])
                    otherTemperatureStates = []
                    for deviceEui in devicesInPlacement:
                        for i in range(0, len(lastTemps)):
                            if (lastTemps[i]['deviceEui'] == deviceEui):
                                otherTemperatureStates.append(lastTemps[i]['temperature'])
                                break
                    if ((otherTemperatureStates == []) or (packetData['temperature'] < min(otherTemperatureStates))):
                        print(otherTemperatureStates)
                        controller[packetData['devicePlacement']].update_value(packetData['temperature'])
                else:
                    controller[packetData['devicePlacement']].update_value(packetData['temperature'])
                
            # Skriv til databesen dersom det ikke er en powerData-melding, eller hvis den aktive effekten i powerData-meldingen er høyere enn 5 W.
            # if (packetData['messageType'] != 'powerData'):
            #     container_name = packetData['devicePlacement']
            #     write_to_db(container_name, packetData)
            # elif (packetData['activePower'] > 5):
            #     container_name = packetData['devicePlacement']
            #     write_to_db(container_name, packetData)

        elif topic == 'gatewayStatus':
            payload = message.payload.decode("utf-8") 
            print(payload)

            time = dt.now()
            time = dt.strftime(time, '%d.%m.%Y %H:%M')
            
            to_file = "\n[{}] : {}".format(time, payload)
            f = open(gatewayFile, 'a')
            f.write(to_file)
            f.close

    # @mqtt.on_log()
    # def handle_logging(client, userdata, level, buf):
    #         print('[MQTT] {}'.format(buf))

# Utsending av "Meter-data-request"
def claimMeterdata(devicePlacement):
    startTime = dt.now().astimezone(pytz.timezone('Europe/Oslo')) # Definerer starttidspunkt med tidssonestempel for Norge
    attempts = 0 # Initialiserer en forsøks-teller
    # Kjør while-løkke så lenge siste pakketype er ulik "powerData" || eller pakken tilhører en annen heat trace sløyfe || eller siste mottatte pakke er eldre enn
    # starttidspunktet til denne løkken || og det er gjennomført inntil 5 forsøk.
    while (((packetData['messageType'] != 'powerData') or (packetData['devicePlacement'] != devicePlacement) or (timeOslo < startTime)) and (attempts < 5)):
        print("packetDate['messageType']: {}, packetDate['devicePlacement']: {}, timeOslo: {}, startTime: {}".format(packetData['messageType'], packetData['devicePlacement'], timeOslo, startTime))
        mqtt.publish('powerSwitch', bytes([4, 2, 0])) # Pakke sendes til Mosquitto MQTT Broker, videre til Node-Red og til slutt til målereléet.
        attempts += 1 # Øker verdien til forsøkstelleren.
        print("Meterdata request were sent. This is the {}. attempt.".format(attempts))
        print("Going to sleep for 6 seconds")
        time.sleep(6) # Løkken sover i 6 sekunder for å vente på pakketransport.
        print("Woke up from sleep")
    # Dersom det ikke kom inn noen ny eller riktig pakke etter 5 forsøk returneres det en feilmelding.
    if ((packetData['messageType'] != 'powerData') or (packetData['devicePlacement'] != devicePlacement) or (timeOslo < startTime)):
        return ("Did not receive meterdata response. Message were sent 5 times")
    # Dersom riktig pakke ble mottatt returneres respons med informasjon om antall forsøk som ble benyttet.
    else:
        return ("Meterdata request has been sent to gateway. Response were received within the {}. attempt.".format(attempts))

# Aktivering av varmekabel der sløyfevariabelen er argumentet (heatTrace1, heatTrace2, osv...)
def activateHeatTrace(devicePlacement):
    startTime = dt.now().astimezone(pytz.timezone('Europe/Oslo')) # Definerer starttidspunkt med tidssonestempel for Norge
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
    # Dersom utgangstilstanden fortsatt er TRUE fungerte ikke aktiveringen, eller det er ikke mottatt bekreftelse på aktivering.
    if (outputState[devicePlacement][0] == True):
        return ("NB! Mottok ingen bekreftelse på aktivering. Aktiveringsmelding ble sendt 5 ganger.")
    # I andre tilfeller er varmekabelen aktivert.
    # Dersom det ble mottatt bekreftelse på aktivering etter starttidspunktet til funksjonen lyktes aktiveringen
    elif (outputState[devicePlacement][1] > startTime):
        return ("Aktiveringsmelding ble sendt til gateway. Bekreftelse ble mottatt etter {}. forsøk.".format(attempts))
    # Dersom aktiveringstidspunktet var før denne funksjonen startet returneres denne beskjeden.
    else:
        return ("Varmekabelen er allerede aktivert.")

# Deaktivering av varmekabel der sløyfevariabelen er argumentet (heatTrace1, heatTrace2, osv...)
def deactivateHeatTrace(devicePlacement):
    startTime = dt.now().astimezone(pytz.timezone('Europe/Oslo')) # Definerer starttidspunkt med tidssonestempel for Norge
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
    # Dersom utgangstilstanden fortsatt er FALSE fungerte ikke deaktiveringen, eller det er ikke mottatt bekreftelse på deaktivering.
    if (outputState[devicePlacement][0] == False):
        return ("NB! Mottok ingen bekreftelse på deaktivering. Deaktiveringsmelding ble sendt 5 ganger.")
    # I andre tilfeller er varmekabelen deaktivert.
    # Dersom det ble mottatt bekreftelse på deaktivering etter starttidspunktet til funksjonen lyktes deaktiveringen
    elif (outputState[devicePlacement][1] > startTime):
        return ("Deaktiveringsmelding ble sendt til gateway. Bekreftelse ble mottatt etter {}. forsøk.".format(attempts))
    # Dersom deaktiveringstidspunktet var før denne funksjonen startet returneres denne beskjeden.
    else:
        return ("Varmekabelen er allerede deaktivert.")

def createController(devicePlacement):
    global controller
    controller[devicePlacement] = PI_controller(devicePlacement, activateHeatTrace, deactivateHeatTrace)
    outputState[devicePlacement] = [False, dt.now().astimezone(pytz.timezone('Europe/Oslo'))]
    print("creating new controller")

def deleteController(devicePlacement):
    global controller
    print("deleting controller from: {}".format(devicePlacement))
    del controller[devicePlacement]

def get_controller(devicePlacement):
    global controller
    #print("Got controllers: {}".format(controller))
    return controller[devicePlacement]


def get_output_state(devicePlacement):
    global outputState
    return outputState[devicePlacement]

def initialisation():
    from dashApps.innstillinger import get_sløyfer, get_settings, get_devices
    global controller, outputState
    controller = {}
    outputState = {}

    settings = get_settings()

    for sløyfe in get_sløyfer():
        for device in settings[sløyfe]['devices']:
            if 'Power Switch' in device.values():
                controller[sløyfe] = PI_controller(sløyfe, activateHeatTrace, deactivateHeatTrace)
                outputState[sløyfe] = [False, dt.now().astimezone(pytz.timezone('Europe/Oslo'))]

packetData = {}
timeOslo = datetime.time()
initialisation()