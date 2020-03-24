from cosmosDB import read_from_db
import pandas as pd

#Leser fra databasen, laster inn antall målinger og hvilken sløyfe.
def update_tempData(antall_målinger, sløyfe_valg):
    query = "SELECT TOP {} * FROM {} WHERE ({}.deviceType = 'tempSensor' AND heatTrace1.deviceEui = '70-b3-d5-80-a0-10-94-46') ORDER BY {}.timeReceived DESC".format(antall_målinger,sløyfe_valg,sløyfe_valg,sløyfe_valg)
    container_name = sløyfe_valg
    items = read_from_db(container_name, query)
    # Definerer litene inne i funsjonen slik de ikke vokser for hver kjøring
    ts=[]
    temp=[]
    ts_UTC=[]
    #sorterer ut relevant informasjon fra "Items" som innehold alt som ble lest fradatabasen
    for i in items:
        temp.append(i['temperature'])
    for i in items:
        ts.append(i['_ts'])
    #Gjør om til datatypen "Date-time" som blir brukt til plotting.
    ts_UTC= pd.to_datetime(ts, unit='s')
    return  ts_UTC,temp