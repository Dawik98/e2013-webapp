from cosmosDB import read_from_db
import pandas as pd

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

    d = {'Time recived, temp': historiskData["Temperatur-Sensor"]["timeReceived"],
        'Temperatur [°C]': historiskData["Temperatur-Sensor"]["temperature"],
        'Time recived, rele': historiskData["Power-Switch"]["timeReceived"],
        'activePower [W]': historiskData["Power-Switch"]["activePower"],
        'reactivePower [VAr]': historiskData["Power-Switch"]["reactivePower"],
        'apparentPower [VA]': historiskData["Power-Switch"]["apparentPower"],
        'activeEnergy [kWh]': historiskData["Power-Switch"]["activeEnergy"],
        'reactiveEnergy [kVAh]': historiskData["Power-Switch"]["reactiveEnergy"],
        'apparentEnergy [VArh]': historiskData["Power-Switch"]["apparentEnergy"],
        'voltage [V]': historiskData["Power-Switch"]["voltage"],
        'current [mA]': historiskData["Power-Switch"]["current"],
        'frequency [f]': historiskData["Power-Switch"]["frequency"],
        'runTime [s]': historiskData["Power-Switch"]["runTime"],
         }
    #Unngår feil på grunn av ulike lengder på listene.
    df = pd.DataFrame.from_dict(data=d, orient='index')
    df=df.transpose()

    return df
