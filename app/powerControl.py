from threading import Thread, Lock
from time import time, sleep
from datetime import datetime as dt
import pytz
from cosmosDB import write_to_db

class PI_controller:
    def __init__(self, devicePlacement, activate_func, deactivate_func, mode='Auto', duty_cycle=1.0):
        self.devicePlacement = devicePlacement

        self.Kp = 0.0 # Proportional forsterkning
        self.Ti = 0.0 # Integraltid
        self.Ts = 0.0 # Samplingstid

        self.setpoint = 0
        self.error = 0

        self.u_p = 0
        self.u_i = 0
        self.u_tot = 0

        # Tilbakekoblingsverdi:
        self.value = 0
        self.value_prev = 0

        self.time_now = time()
        self.time_prev = 0

        self.dutycycle = duty_cycle # Dutycycle i minutter
        self.lock = Lock() # Lock for u_tot and dutycycle

        self.mode = mode
        self.run_actuation = False # Reléstyring er "default off"

        self.actuation_control = Thread(target=self.actuationControl)
        self.actuation_control.start()

        self.activate_func = activate_func
        self.deactivate_func = deactivate_func

    def get_device_placement(self):
        return self.devicePlacement

    def update_parameters(self, Kp, Ti):
        self.Kp = Kp # Proporsjonal forsterkning
        self.Ti = Ti # Integraltid
    
    def update_value(self, value):
        print("Updating measure value")
        self.value_prev = self.value
        self.value = round(value,2)
        self.calculate_u_tot()

    def update_setpoint(self, setpoint):
        self.setpoint = round(setpoint,2)
        self.calculate_u_tot()

    def get_sample_time(self):
        self.time_prev = self.time_now
        self.time_now = time()
        self.Ts = self.time_now - self.time_prev

    # Proporsjonalbidrag
    def proportional(self):
        u_p = self.Kp * self.error
        self.u_p = round(u_p,2)
        
    # Intagralbidrag
    def integral(self):
        try:
            u_i = self.Kp * self.Ts / self.Ti * self.error + self.u_i
            self.u_i = round(u_i,2)

            # Anti windup:
            if u_i > 100.0:
                self.u_i = 100.0
            elif u_i < 0.0:
                self.u_i = 0.0

        except ZeroDivisionError:
            self.u_i = 0.00

    def bumpless(self, u_tot):
        # Kjør denne funksjonen hvis det byttes til regulatorstyring etter å ha brukt manuelt pådrag
        # "Reset" tida og bruk integralvirkning som det gamle pådraget
        self.u_i = u_tot
        self.get_sample_time()
            
    # Kalkuler avvik
    def get_error(self):
        error = self.setpoint - self.value
        self.error = round(error,2)

    def calculate_u_tot(self):
        """
        calculate_u_tot() kalkulerer totalt pådragstall
        """
        if self.mode == 'Auto':
            self.get_sample_time()
            self.get_error()

            # Kalkuler proporsjonal-, integralbidraget til pådraget.
            self.proportional()
            print("Proporsjonalbidraget er {} %".format(self.u_p))
            self.integral()
            print("Integralbidraget er {} %".format(self.u_i))
            u_tot = self.u_p + self.u_i

            # Anti windup:
            if u_tot > 100.0:
                u_tot = 100.0
            elif u_tot < 0.0:
                u_tot = 0.0
            else:
                u_tot = round(u_tot, 2)
            self.set_u_tot(u_tot)
            # Dersom automatisk av/på reglering er aktivert skriver regulator-data som item til databasen, slik at dette senere kan plottes under "Historikk"
            if self.run_actuation:
                timestamp = dt.now()
                timestamp = timestamp.astimezone(pytz.timezone('Europe/Oslo'))
                timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')             # Tidspunkt for nytt pådrag
                controllerData = {
                    'devicePlacement': self.devicePlacement,
                    'messageType': "controllerData",
                    'timeReceived': timestamp,
                    'setpoint': self.setpoint,
                    'actuation': u_tot
                }
                # Skriver til databasen med container lik devicePlacement.
                write_to_db(self.devicePlacement, controllerData)
    
    def change_mode(self, mode, actuation=0.0):
        """
        change_mode() benyttes ved skifte av regulatormodus.
        """
        if mode == 'Auto':
            print("Ny regulatormodus: Auto, Tidligere pådrag: {}".format(actuation))
            self.bumpless(actuation)
            self.mode = mode
        elif mode == 'Manual':
            print("Ny regulatormodus: Manuell, Pådrag: {}".format(actuation))
            self.set_u_tot(actuation)
            self.mode = 'Manual'
        else:
            print("Ugylding regulatormodus!")

    def actuationControl(self):
        """
        actuationControl() skrur reléet av og på i en syklus (dutycycle) avhengig av pådragstall.
        Funksjonen kjøres som en individuell tråd. Styringen av reléet kjøres avhengig av tilstanden til self.run_actuation.
        """
        while True:
            if self.run_actuation:
                dutycycle = self.get_dutycycle() * 60
                actuation = self.get_u_tot()
                t_on = (actuation/100) * dutycycle
                t_off = dutycycle - t_on
                if (t_on != 0):
                    self.activate_func(self.devicePlacement)
                    print("{} will be on for {} seconds.".format(self.devicePlacement, t_on))
                    sleep(t_on)
                    print("Woke up from on-time sleep")
                if (t_off != 0):
                    self.deactivate_func(self.devicePlacement)
                    print("{} will be off for {} seconds.".format(self.devicePlacement, t_off))
                    sleep(t_off)
                    print("Woke up from off-time sleep")
            else:
                sleep(1)

    def set_dutycycle(self, dutycycle):
        """
        set_dutycycle() setter ny dutycycle til reléstyringen. Funksjonen benytter lock for sikker behandling av delte variabler.
        """
        self.lock.acquire()
        try:
            self.dutycycle = dutycycle
            print("New dutycycle is set: {} minutes".format(dutycycle))
        finally:
            self.lock.release()

    def get_dutycycle(self):
        """
        get_dutycycle() returnerer dutycycle til reléstyringen. Funksjonen benytter lock for sikker behandling av delte variabler.
        """
        self.lock.acquire()
        try:
            return self.dutycycle
        finally:
            self.lock.release()

    def set_u_tot(self, u_tot):
        """
        set_u_tot() setter nytt totalt pådragstall i prosent. Funksjonen benytter lock for sikker behandling av delte variabler.
        """
        self.lock.acquire()
        try:
            self.u_tot = u_tot
        finally:
            self.lock.release()

    def get_u_tot(self):
        """
        get_u_tot() returnerer totalt pådragstall i prosent. Funksjonen benytter lock for sikker behandling av delte variabler.
        """
        self.lock.acquire()
        try:
            return self.u_tot
        finally:
            self.lock.release()


    def stop(self):
        self.run_actuation = False
        print("Actuation controller is not running")

    def start(self):
        self.run_actuation = True
        print("Actuaton controller is running")