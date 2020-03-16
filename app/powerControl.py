from mqtt import *
from threading import Timer

def powerControl(actuation, dutycycle):
    while (regMode == High):
        # Skru varmekabel på
        activateHeatTrace()
        Timer(actuation/100 * dutycycle)
        # Skru av varmekabel
        deactivateHeatTrace()
        Timer((1 - actuation/100) * dutycycle)