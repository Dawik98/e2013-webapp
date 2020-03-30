from cosmosDB import read_from_db
import pandas as pd

#Funksjon som brukes til å laste ny data inn i plot til måle rele. Queryer databasen for alle målinger ettersom tilkoblingen er det som krever tid, så kan en bytte fritt mellom ulike målinger. 
#Powerwitch data Må gjøres modulært
def update_meterData(sløyfe_valg, fra_dato, til_dato):

    if til_dato == '':
        til_dato=pd.datetime.now()
    
    query = "SELECT * FROM {0} WHERE ({0}.deviceType = 'powerSwitch' AND {0}.deviceEui = '70-b3-d5-8f-f1-00-1e-78' AND {0}.timeReceived >= '{1}' AND {0}.timeReceived <= '{2}' AND {0}.messageType ='powerData') ORDER BY {0}.timeReceived DESC".format(sløyfe_valg,fra_dato, til_dato)
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
    _ts=[]
    

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
            "_ts":_ts,
    }
    #Sorterer riktige målinger til riktig liste. Løper gjennom meterData. 
    for key, value in meterData.items():
        #print(key)
        for i in items:
            meterData[key].append(i[key])

    #Gjør om til kW for aktiv og tilsynelatende energi, siden de akkumuleres over tid.   
    meterData = {key: (pd.Series(value) * 0.001).tolist() if key =='activeEnergy' or key =='apparentEnergy' else value for key, value in meterData.items()} 
    return meterData
