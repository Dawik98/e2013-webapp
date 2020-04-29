from cosmosDB import read_from_db
import pandas as pd
import pytz
from datetime import datetime


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
