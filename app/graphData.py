from cosmosDB import read_from_db
import pytz
from datetime import datetime
from dashApps.innstillinger import get_temp_sensors_in_placement

#from cosmosDB import read_from_db
import pandas as pd
#import pytz
#from datetime import datetime

#from cosmosDB import read_from_db
#import pandas as pd

#from cosmosDB import read_from_db
#from dashApps.innstillinger import get_temp_sensors_in_placement
#import pandas as pd

def update_tempData(sløyfe_valg, fra_dato, til_dato):
    # Henter device-eui-er til alle temperatursensorene i kretsen
    tempSensors = get_temp_sensors_in_placement(sløyfe_valg)
    # Basert på ønsket måle periode, og sløyfe queryer vi databasen for data.
    query = "SELECT {0}.temperature, {0}.deviceEui, {0}.timeReceived FROM {0} WHERE ({0}.deviceType = 'tempSensor' AND {0}.timeReceived >= '{1}' AND {0}.timeReceived <= '{2}') ORDER BY {0}.timeReceived DESC".format(sløyfe_valg, fra_dato, til_dato)
    items = read_from_db(sløyfe_valg, query)
    # Sorterer temperaturdata etter eui i et dictionary. Hver eui har temperatur-liste og mottakstidspunkt-liste
    tempData={}
    for eui in tempSensors:
        tempData[eui] = {
            'temperature':[],
            'timeReceived':[]
        }
        for i in range(0, len(items)):
            if (items[i]['deviceEui'] == eui):
                tempData[eui]['temperature'].append(items[i]['temperature'])
                tempData[eui]['timeReceived'].append(items[i]['timeReceived'])     
    return  tempData


def update_meterData(sløyfe_valg, fra_dato, til_dato):     
    # Basert på ønsket måleperiode, og sløyfe queryer vi databasen for data.
    query = "SELECT * FROM {0} WHERE ({0}.messageType ='powerData' AND {0}.timeReceived >= '{1}' AND {0}.timeReceived <= '{2}') ORDER BY {0}.timeReceived DESC".format(sløyfe_valg,fra_dato, til_dato)
    items = read_from_db(sløyfe_valg, query)
    # Definerer listene og dictonaryen i funksjonen for å nulstille lengden.
    # Dictonary som brukes for å lage meterdata dictonaryet, på denne måten får vi samme navn på listen som nøkkelen som holder den.
    meterData={
        "activePower": [], 
        "reactivePower": [],
        "apparentPower": [],
        "activeEnergy": [],
        "apparentEnergy": [],
        "reactiveEnergy": [],
        "voltage": [],
        "current": [],
        "frequency": [],
        "runTime": [],
        "timeReceived": [],
    }
    # Sorterer riktige målinger til riktig liste. Løper gjennom meterData. 
    for key in meterData:
        for i in items:
            meterData[key].append(i[key])
    # Gjør om til kW for aktiv og tilsynelatende energi, siden de akkumuleres over tid.   
    meterData = {key: (pd.Series(value) * 0.001).tolist() if key =='activeEnergy' or key =='apparentEnergy' else value for key, value in meterData.items()}
    return meterData



# Funksjon som brukes til å laste ny data inn i historisk plot.
# Henter ALL data fra databasen slik grafen blir responsive i ettertid.
def update_historiskData(sløyfe_valg):
    # Henter temperaturdata (messageType = dataLog) og effektdata (messageType = powerData) fra database
    query = "SELECT {0}.timeReceived, {0}.messageType, {0}.deviceEui, {0}.timestamp, {0}.setpoint, {0}.actuation, {0}.temperature, {0}.activePower, {0}.reactivePower, {0}.apparentPower, {0}.activeEnergy, {0}.reactiveEnergy, {0}.apparentEnergy, {0}.voltage, {0}.current, {0}.frequency, {0}.runTime FROM {0} WHERE (({0}.messageType = 'dataLog') OR ({0}.messageType = 'powerData') OR ({0}.messageType = 'controllerData')) ORDER BY {0}.timeReceived DESC".format(sløyfe_valg)
    items = read_from_db(sløyfe_valg, query)

    # Forhåndsdefinerer et dictionary "historiskData" med tomme verdilister.
    # "historiskData" inneholder to dictionary's; ett for målerelé og et for temperatursensorer.
    # Dictionary-et for temperatursensorer er delt opp i flere dictionary's; ett for hver tilknyttet temperatursensor
    tempDeviceEuis = get_temp_sensors_in_placement(sløyfe_valg)
    tempSensors = {}
    for eui in tempDeviceEuis:
        tempSensors[eui] = {
            "temperature":[],
            "timeReceived":[],
        }
    historiskData = {
        "Power-Switch": {
            "activePower":[], 
            "reactivePower":[],
            "apparentPower":[],
            "activeEnergy":[],
            "apparentEnergy":[],
            "reactiveEnergy":[],
            "voltage":[],
            "current":[],
            "frequency":[],
            "runTime":[],
            "timeReceived":[],
        },
        "Temperatur-Sensor": tempSensors,
        "controllerData":{
                "actuation":[],
                "setpoint":[],
                "timestamp":[],
            }
    }
    # Går igjennom samtlige dictionary's i mottatt data fra database (items) og sorterer data.
    for i in range(0, len(items)):
        if (items[i]['messageType'] == 'dataLog'):
            for eui in historiskData['Temperatur-Sensor']:
                if (items[i]['deviceEui'] == eui):
                    historiskData['Temperatur-Sensor'][eui]['temperature'].append(items[i]['temperature'])
                    historiskData['Temperatur-Sensor'][eui]['timeReceived'].append(items[i]['timeReceived'])
        elif (items[i]['messageType'] == 'controllerData'):
            for messurment in historiskData['controllerData']:
                historiskData['controllerData'][messurment].append(items[i][messurment])
        else:
            for messurment in historiskData['Power-Switch']:
                historiskData['Power-Switch'][messurment].append(items[i][messurment])
    print(historiskData["controllerData"])            
    #endrer fra Wh til kWh
    historiskData['Power-Switch'] = {key: (pd.Series(value) * 0.001).tolist() if key =='activeEnergy' or key =='apparentEnergy' else value for key, value in historiskData["Power-Switch"].items()}    
    return historiskData


#Funksjon som brukes til å laste ny data inn i historisk plot 
def print_historiskData(sløyfe_valg,til_dato, fra_dato):
    #Deler inn i to querys for å skille mellom tidsstempelene
    #henter tempdata
    query = "SELECT * FROM {0} WHERE ({0}.deviceType = 'tempSensor' AND {0}.timeReceived >= '{2}' AND {0}.timeReceived <= '{1}') ORDER BY {0}.timeReceived DESC".format(sløyfe_valg, fra_dato, til_dato)
    container_name = sløyfe_valg
    items_temp = read_from_db(container_name, query)
    #Hente meterData
    query = "SELECT * FROM {0} WHERE ({0}.messageType ='powerData' AND {0}.timeReceived >= '{2}' AND {0}.timeReceived <= '{1}') ORDER BY {0}.timeReceived DESC".format(sløyfe_valg, fra_dato, til_dato)
    container_name = sløyfe_valg
    items_meter = read_from_db(container_name, query)

    #definerer listene og dictonaryen i funksjonen for å nulstille lengden.
    temperature=[]
    activePower=[]
    reactivePower=[]
    apparentPower=[]
    activeEnergy=[]
    apparentEnergy=[]
    reactiveEnergy=[]
    voltage=[]
    current=[]
    frequency=[]
    runTime=[]
    _tsTemp=[]
    _tsMeter=[]
    
    #Dictonary med et dictonary til måledata fra rele, og et til tempsensor.
    historiskData={
            "Power-Switch":{
            "activePower":activePower, 
            "reactivePower":reactivePower,
            "apparentPower":apparentPower,
            "activeEnergy":activeEnergy,
            "apparentEnergy":apparentEnergy,
            "reactiveEnergy":reactiveEnergy,
            "voltage":voltage,
            "current":current,
            "frequency":frequency,
            "runTime":runTime,
            "timeReceived":_tsMeter,
            },
            "Temperatur-Sensor":{
            "temperature":temperature,
            "timeReceived":_tsTemp,
            },
    }
    #Sorterer riktige målinger til riktig liste. Løper gjennom meterData. 
    for key, value in historiskData["Power-Switch"].items():
        #print(key)
        for i in items_meter:
            historiskData["Power-Switch"][key].append(i[key])
    #Gjør om til kW for aktiv og tilsynelatende energi, siden de akkumuleres over tid.   
    historiskData["Power-Switch"] = {key: (pd.Series(value) * 0.001).tolist() if key =='activeEnergy' or key =='apparentEnergy' else value for key, value in historiskData["Power-Switch"].items()} 
    
    #Sorterer riktige målinger til riktig liste. Løper gjennom meterData. 
    for key, value in historiskData["Temperatur-Sensor"].items():
        for i in items_temp:
            historiskData["Temperatur-Sensor"][key].append(i[key])
    
    #Sorterer riktige målinger til riktig liste. Løper gjennom controller data. 
    for key, value in historiskData["Power-Controller"].items():
        for i in items_temp:
            historiskData["Power-Controller"][key].append(i[key])

    d = {'Time recived, temp': historiskData["Temperatur-Sensor"]["timeReceived"],
        'Temperature [°C]': historiskData["Temperatur-Sensor"]["temperature"],
        'Time recived, meter-relay': historiskData["Power-Switch"]["timeReceived"],
        'Active Power [W]': historiskData["Power-Switch"]["activePower"],
        'Reactive Power [VAr]': historiskData["Power-Switch"]["reactivePower"],
        'Apparent Power [VA]': historiskData["Power-Switch"]["apparentPower"],
        'Active Energy [kWh]': historiskData["Power-Switch"]["activeEnergy"],
        'Reactive Energy [kVArh]': historiskData["Power-Switch"]["reactiveEnergy"],
        'Apparent Energy [kVAh]': historiskData["Power-Switch"]["apparentEnergy"],
        'Voltage [V]': historiskData["Power-Switch"]["voltage"],
        'Current [mA]': historiskData["Power-Switch"]["current"],
        'Frequency [f]': historiskData["Power-Switch"]["frequency"],
        'Runtime [s]': historiskData["Power-Switch"]["runTime"],
         }
    #Unngår feil på grunn av ulike lengder på listene. "Dobbel transponering"
    df = pd.DataFrame.from_dict(data=d, orient='index')
    df=df.transpose()

    return df

