from cosmosDB import read_from_db
import pytz
from datetime import datetime
from dashApps.innstillinger import get_temp_sensors_in_placement

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
