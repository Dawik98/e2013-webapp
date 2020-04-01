import json

def print_settings():
    with open('app/settings.txt') as json_file:
        data = json.load(json_file)
        print(json.dumps(data, indent=4))

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

#def update_alarms(sløyfe, max_value, min_value):
#    alarm_data = {'max_val':max_value, 'min_val': min_value}
#    with open('app/settings.txt', 'r+') as settings_file:
#        settings = json.load(settings_file)
#        settings[sløyfe]['alarm_values'].append(device_data)
#        settings_file.seek(0)
#        json.dump(settings, settings_file)

def change_alarm_values(sløyfe, min_value, max_value):
    alarm_values = {'min_val':min_value, 'max_val': max_value}
    with open('app/settings.txt', 'r+') as settings_file:
        settings = json.load(settings_file)
        settings[sløyfe]['alarm_values'] = alarm_values
        settings_file.seek(0)
        json.dump(settings, settings_file)

def get_alarms(sløyfe):
    alarms = []
    with open('app/settings.txt') as json_file:
        data = json.load(json_file)
        for key, value in data[sløyfe]['alarm_values'].items():
            alarms.append(value)

    return alarms

change_alarm_values('heatTrace1', 10, 40)
print_settings()
print(get_alarms('heatTrace1'))