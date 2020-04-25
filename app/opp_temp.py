from cosmosDB import read_from_db
import pandas as pd
import pytz
from datetime import datetime
from dashApps.innstillinger import get_temp_sensors_in_placement

def update_tempData(sløyfe_valg, fra_dato, til_dato):
    # Dersom ingenting er skrevet i feltet med t "til dato" plotter vi til tidspunket nå (LIVE)
    if til_dato == '':
        til_dato_UTC = datetime.now()
        til_dato = til_dato_UTC.astimezone(pytz.timezone('Europe/Oslo'))
        til_dato=til_dato.strftime("%Y-%m-%d %H:%M:%S")
    #sjekker om det er flere tempsensorer
    tempSensors = get_temp_sensors_in_placement(sløyfe_valg)
    #Basert på ønsket måle periode, og sløyfe queryer vi databasen for data.
    query = "SELECT {0}.temperature, {0}.deviceEui, {0}.timeReceived FROM {0} WHERE ({0}.deviceType = 'tempSensor' AND {0}.timeReceived >= '{1}' AND {0}.timeReceived <= '{2}') ORDER BY {0}.timeReceived DESC".format(sløyfe_valg, fra_dato, til_dato)
    container_name = sløyfe_valg
    items=[]
    items = read_from_db(container_name, query)
    # Definerer litene inne i funsjonen slik de ikke vokser for hver kjøring
    Data={}
    for EUI in tempSensors:
        Data[EUI] = {
            'temperature':[],
            'ts':[]
        }
        for i in range(0, len(items)):
            if (items[i]['deviceEui'] == EUI):
                Data[EUI]['temperature'].append(items[i]['temperature'])
                Data[EUI]['ts'].append(items[i]['timeReceived'])     
    return  Data
