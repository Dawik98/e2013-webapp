import json

#data = {'heatTrace1' : 
#            {'devices' : [{'device_eui':'70-b3-d5-80-a0-10-94-3a', 'deviceType': 'tempSensor'}],
#            'alarm_values' : [10,30]}
#        }

#data = {'device_eui':'70-b3-d5-80-a0-10-94-3d', 'deviceType': 'tempSensor'}

#data = {'heatTrace2' : 
#            {'devices' : [],
#            'alarm_values' : []}
#        }

{"heatTrace1": {"devices": [{"device_eui": "70-b3-d5-80-a0-10-94-3a", "deviceType": "tempSensor"}, {"device_eui": "70-b3-d5-80-a0-10-94-3d", "deviceType": "tempSensor"}]}, "heatTrace2": {"devices": [], "alarm_values": []}}

data = [11,30]

#with open('app/settings.txt', 'r+') as settings_file:
#    settings = json.load(settings_file)
#    settings['heatTrace1']['alarm_values'] = data
#    settings_file.seek(0)
#    json.dump(settings, settings_file)

def add_sløyfe(sløyfe):
    data = {sløyfe : 
                {'devices' : [],
                'alarm_values' : []}
            }
    with open('app/settings.txt', 'r+') as settings_file:
        settings = json.load(settings_file)
        settings.update(data)
        settings_file.seek(0)
        json.dump(settings, settings_file)

def remove_sløyfe(sløyfe):
    with open('app/settings.txt', 'r+') as settings_file:
        settings = json.load(settings_file)
        #del settings[sløyfe]
        settings.pop(sløyfe, None)
        settings_file.seek(0)
        settings_file.truncate(0) #clear file
        json.dump(settings, settings_file)

def add_device(sløyfe, device_eui, device_type):
    device_data = {'device_eui':device_eui, 'deviceType': device_type}
    with open('app/settings.txt', 'r+') as settings_file:
        settings = json.load(settings_file)
        settings[sløyfe]['devices'].append(device_data)
        settings_file.seek(0)
        json.dump(settings, settings_file)

def remove_device(sløyfe, device_eui):
    with open('app/settings.txt', 'r+') as settings_file:
        settings = json.load(settings_file)
        n = 0
        for i in settings[sløyfe]['devices']:
            if i['device_eui'] == device_eui:
                del settings[sløyfe]['devices'][n]
            n+=1
        settings_file.seek(0)
        settings_file.truncate(0) #clear file
        json.dump(settings, settings_file)

#add_device('heatTrace2', '111', 'test')
#remove_device('heatTrace2', '111')

with open('app/settings.txt') as json_file:
    data = json.load(json_file)
    print(json.dumps(data, indent=4))