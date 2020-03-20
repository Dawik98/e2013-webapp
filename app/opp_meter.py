from cosmosDB import read_from_db
import pandas as pd


#Powerwitch data Må gjøres modulært
def update_meterData(antall_målinger, sløyfe_valg):
    query = "SELECT TOP {} * FROM {} WHERE ({}.deviceType = 'powerSwitch' AND {}.deviceEui = '70-b3-d5-8f-f1-00-1e-78' AND {}.messageType ='powerData') ORDER BY {}.timeReceived DESC".format(antall_målinger,sløyfe_valg,sløyfe_valg,sløyfe_valg,sløyfe_valg,sløyfe_valg)
    container_name = sløyfe_valg
    items = read_from_db(container_name, query)
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

    for key, value in meterData.items():
        #print(key)
        for i in items:
            meterData[key].append(i[key])

    #Gjør om til kW   
    meterData = {key: (pd.Series(value) * 0.001).tolist() if key =='activeEnergy' or key =='apparentEnergy' else value for key, value in meterData.items()} 
    return meterData
