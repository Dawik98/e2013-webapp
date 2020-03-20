from cosmosDB import read_from_db
import pandas as pd


def update_tempData(antall_målinger, sløyfe_valg):
    #if  antall_målinger_pre != antall_målinger:
    #print("Kjører funksjon")
    query = "SELECT TOP {} * FROM {} WHERE ({}.deviceType = 'tempSensor' AND heatTrace1.deviceEui = '70-b3-d5-80-a0-10-94-46') ORDER BY {}.timeReceived DESC".format(antall_målinger,sløyfe_valg,sløyfe_valg,sløyfe_valg)
    container_name = sløyfe_valg
    items = read_from_db(container_name, query)
    ts=[]
    temp=[]
    ts_UTC=[]
    for i in items:
        temp.append(i['temperature'])
    for i in items:
        ts.append(i['_ts'])
    ts_UTC= pd.to_datetime(ts, unit='s')
    #ts_ht1OSLO = ts_ht1UTC.astimezone(pytz.timezone('Europe/Oslo'))
    #print(temp_ht1)
    return  ts_UTC,temp