from cosmosDB import read_from_db
import pandas as pd
import pytz
from datetime import datetime


def update_meterData(sløyfe_valg, fra_dato, til_dato):
    # Dersom ingenting er skrevet i feltet med t "til dato" plotter vi til tidspunket nå (LIVE)
    if til_dato == '':
        til_dato_UTC = datetime.now()
        til_dato = til_dato_UTC.astimezone(pytz.timezone('Europe/Oslo'))
        
    #Basert på ønsket måle periode, og sløyfe queryer vi databasen for data.
    query = "SELECT * FROM {0} WHERE ({0}.deviceType = 'powerSwitch' AND {0}.timeReceived >= '{1}' AND {0}.timeReceived <= '{2}' AND {0}.messageType ='powerData') ORDER BY {0}.timeReceived DESC".format(sløyfe_valg,fra_dato, til_dato)
    container_name = sløyfe_valg
    items=[]
    items = read_from_db(container_name, query)
    #definerer listene og dictonaryen i funksjonen for å nulstille lengden.
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
    timeReceived=[]
    
    #dictonary som brukes for å lage meterdata dictonaryet, på denne måten får vi samme navn på listen som nøkkelen som holder den.
    meterData={"activePower":activePower, 
            "reactivePower":reactivePower,
            "apparentPower":apparentPower,
            "activeEnergy":activeEnergy,
            "apparentEnergy":apparentEnergy,
            "reactiveEnergy":reactiveEnergy,
            "voltage":voltage,
            "current":current,
            "frequency":frequency,
            "runTime":runTime,
            "timeReceived":timeReceived,
    }
    #Sorterer riktige målinger til riktig liste. Løper gjennom meterData. 
    for key, value in meterData.items():
        #print(key)
        for i in items:
            meterData[key].append(i[key])

    #Gjør om til kW for aktiv og tilsynelatende energi, siden de akkumuleres over tid.   
    meterData = {key: (pd.Series(value) * 0.001).tolist() if key =='activeEnergy' or key =='apparentEnergy' else value for key, value in meterData.items()} 
    return meterData
