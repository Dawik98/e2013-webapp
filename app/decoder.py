from datetime import datetime
import pytz


def decoder(payload):
    devices = {
        '70-b3-d5-80-a0-10-94-3a': ['heatTrace1', 'tempSensor'],
        '70-b3-d5-80-a0-10-94-46': ['heatTrace1', 'tempSensor'],
        '70-b3-d5-8f-f1-00-1e-78': ['heatTrace1', 'powerSwitch'],
    }
    timeUTC = datetime.strptime(payload['time'], '%Y-%m-%dT%H:%M:%S.%f%z')
    timeOslo = timeUTC.astimezone(pytz.timezone('Europe/Oslo'))
    
    packetData = {
        'deviceEui': payload['deveui'],
        'devicePlacement': devices[payload['deveui']][0],
        'deviceType': devices[payload['deveui']][1],
        'timeReceived': timeOslo.strftime('%Y-%m-%d %H:%M:%S'),
    }
    data = bytes(payload['data'])

    if (packetData['deviceType'] == 'tempSensor'):
        if (data[0] == 0x00): packetData['messageType'] = 'startMessage'
        elif (data[0] == 0x01):
            packetData['messageType'] = 'dataLog'
            packetData['batteryLevel'] = int.from_bytes(data[1:2], byteorder='big', signed=False) * 100/256
        dataLength = len(data)
        packetData['temperature'] = int.from_bytes(data[dataLength-2:dataLength], byteorder='big', signed=True) / 16

        # Håndtering av alarm-verdier
        from dashApps.innstillinger import get_alarms
        sløyfe = packetData['devicePlacement']
        alarm_values = get_alarms(sløyfe)
        temp = packetData['temperature']
        if temp <= alarm_values[0] or temp >= alarm_values[1]:
            packetData['alarmValue'] = True
            packetData['alarmConfirmed'] = False
        else:
            packetData['alarmValue'] = False





    elif (packetData['deviceType'] == 'powerSwitch'):
        # Decode sending time
        timeSent = {
            'year': 2000 + (data[4] >> 1),
            'month': ((data[4] & 0x01) << 3) | (data[3] >> 5),
            'day': data[3] & 0x1f,
            'hours': data[2] >> 3,
            'minutes': ((data[2] & 0x7) << 3) | (data[1] >> 5),
            'seconds': (data[1] & 0x1f) * 2,
        }
        datetimeSent = datetime(timeSent['year'], timeSent['month'], timeSent['day'], timeSent['hours'], timeSent['minutes'], timeSent['seconds'])
        packetData['timeSent']= datetimeSent.strftime('%Y-%m-%d %H:%M:%S')
        
        if (data[0] == 0x01):
            # This is a time-sync-request message
            packetData['messageType'] = 'timeSyncRequest'
        elif (data[0] == 0x09):
            # This is a power-data message
            packetData['messageType'] = 'powerData'

            period = int.from_bytes(data[27:29], byteorder='little', signed=False)
            packetData['activeEnergy'] = int.from_bytes(data[5:9], byteorder = 'little', signed = True)
            packetData['reactiveEnergy'] = int.from_bytes(data[9:13], byteorder = 'little', signed = True)
            packetData['apparentEnergy'] = int.from_bytes(data[13:17], byteorder = 'little', signed = True)
            packetData['activePower'] = int.from_bytes(data[17:19], byteorder = 'little', signed = True)
            packetData['reactivePower'] = int.from_bytes(data[19:21], byteorder = 'little', signed = True)
            packetData['apparentPower'] = int.from_bytes(data[21:23], byteorder = 'little', signed = True)
            packetData['voltage'] = int.from_bytes(data[23:25], byteorder = 'little', signed = False) / 10
            packetData['current'] = int.from_bytes(data[25:27], byteorder = 'little', signed = False)
            packetData['frequency'] = 1 / (period/1000000)
            packetData['runTime'] = int.from_bytes(data[29:33], byteorder = 'little', signed = False)

        elif (data[0] == 0x0A):
            # This is a input-output-data message
            packetData['messageType'] = 'ioData'

            if (data[5]): packetData['input'] = True
            else: packetData['input'] = False

            if (data[9]): packetData['output'] = True
            else: packetData['output'] = False
    
    return packetData, timeOslo
