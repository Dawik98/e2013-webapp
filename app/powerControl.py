from mqtt import *
from threading import Timer

def powerControl(actuation, dutycycle):
    while (auto == High):
        # Skru varmekabel på
        activateHeatTrace()
        Timer(actuation/100 * dutycycle)
        # Skru av varmekabel
        deactivateHeatTrace()
        Timer((1 - pådrag/100%) * 1 min)