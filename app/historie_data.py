from cosmosDB import read_from_db
from dashApps.innstillinger import get_temp_sensors_in_placement
import pandas as pd

# Funksjon som brukes til å laste ny data inn i historisk plot.
# Henter ALL data fra databasen slik grafen blir responsive i ettertid.
def update_historiskData(sløyfe_valg):
    # Henter temperaturdata (messageType = dataLog) og effektdata (messageType = powerData) fra database
    query = "SELECT {0}.timeReceived, {0}.messageType, {0}.deviceEui, {0}.temperature, {0}.activePower, {0}.reactivePower, {0}.apparentPower, {0}.activeEnergy, {0}.reactiveEnergy, {0}.apparentEnergy, {0}.voltage, {0}.current, {0}.frequency, {0}.runTime FROM {0} WHERE (({0}.messageType = 'dataLog') OR ({0}.messageType = 'powerData')) ORDER BY {0}.timeReceived DESC".format(sløyfe_valg)
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
        "Temperatur-Sensor": tempSensors
    }
    # Går igjennom samtlige dictionary's i mottatt data fra database (items) og sorterer data.
    for i in range(0, len(items)):
        if (items[i]['messageType'] == 'dataLog'):
            for eui in historiskData['Temperatur-Sensor']:
                if (items[i]['deviceEui'] == eui):
                    historiskData['Temperatur-Sensor'][eui]['temperature'].append(items[i]['temperature'])
                    historiskData['Temperatur-Sensor'][eui]['timeReceived'].append(items[i]['timeReceived'])
        else:
            for key in historiskData['Power-Switch']:
                historiskData['Power-Switch'][key].append(items[i][key])
    historiskData['Power-Switch'] = {key: (pd.Series(value) * 0.001).tolist() if key =='activeEnergy' or key =='apparentEnergy' else value for key, value in historiskData["Power-Switch"].items()}    
    return historiskData
