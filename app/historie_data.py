from cosmosDB import read_from_db
import pandas as pd

#Funksjon som brukes til å laste ny data inn i plot til måle rele. Queryer databasen for alle målinger ettersom tilkoblingen er det som krever tid, så kan en bytte fritt mellom ulike målinger. 
#Powerwitch data Må gjøres modulært
def update_historiskData(sløyfe_valg):
    query = "SELECT * FROM {0} WHERE ({0}.deviceType = 'tempSensor' AND heatTrace1.deviceEui = '70-b3-d5-80-a0-10-94-46') ORDER BY {0}.timeReceived DESC".format(sløyfe_valg)
    container_name = sløyfe_valg
    items_temp = read_from_db(container_name, query)
    #Hente meterData
    query = "SELECT * FROM {0} WHERE {0}.messageType ='powerData' ORDER BY {0}.timeReceived DESC".format(sløyfe_valg)
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
            "_ts":_tsMeter,
            },
            "Temperatur-Sensor":{
            "temperature":temperature,
            "_ts":_tsTemp,
            }
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
    
    return historiskData

historiskData=update_historiskData("heatTrace1")
