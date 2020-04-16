import json

settingsFile = 'app/settings.txt' # Lokalt

def print_settings():
    """
    print_settings printer innstillinger som ligger i 'settings.txt' på en lesbar måte
    """
    with open(settingsFile) as json_file:
        data = json.load(json_file)
        print(json.dumps(data, indent=4))

def get_devices():
    devices = {}
    with open(settingsFile) as json_file:
        data = json.load(json_file)
        for sløyfe in data:

            for device in data[sløyfe]['devices']:
                devices[device['device_eui']] = [sløyfe, device['deviceType']]
    return devices



print_settings()
print(get_devices())