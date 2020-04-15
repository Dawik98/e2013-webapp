from cosmosDB import read_from_db
import pandas as pd

def update_tempData(sløyfe_valg, fra_dato, til_dato):
    # Dersom ingenting er skrevet i feltet med t "til dato" plotter vi til tidspunket nå (LIVE)
    if til_dato == '':
        til_dato=pd.datetime.now()
    #Basert på ønsket måle periode, og sløyfe queryer vi databasen for data.
    query = "SELECT * FROM {0} WHERE ({0}.deviceType = 'tempSensor' AND {0}.timeReceived >= '{1}' AND {0}.timeReceived <= '{2}') ORDER BY {0}.timeReceived DESC".format(sløyfe_valg, fra_dato, til_dato)
    container_name = sløyfe_valg
    items=[]
    items = read_from_db(container_name, query)
    # Definerer litene inne i funsjonen slik de ikke vokser for hver kjøring
    ts=[]
    temp=[]
    ts_UTC=[]
    #sorterer ut relevant informasjon fra "Items" som innehold alt som ble lest fra databasen
    for i in items:
        temp.append(i['temperature'])
    for i in items:
            ts.append(i['timeReceived'])
    
    ts_UTC=ts
    
    return  ts_UTC,temp
