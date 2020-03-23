from threading import Timer, Thread, Lock
from time import time, ctime, sleep

import sys

#from mqttCommunication import activateHeatTrace, deactivateHeatTrace

class PI_controller:

    def __init__(self, reg_name, activate_func, deactivate_func, mode='Auto', duty_cycle=1.0, log_results=False):

        self.name = reg_name
        self.log_results = log_results

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

        self.dutycycle = duty_cycle # min
        self.lock = Lock() # Lock for u_tot and dutycycle

        self.mode = mode
        self.run_actuation = False

        self.actuation_control = Thread(target=self.actuationControl)
        self.actuation_control.start()

        self.activate_func = activate_func
        self.deactivate_func = deactivate_func

    def get_reg_name(self):
        return self.name

    # Skriv til loggen
    def writer(self, data):
         file = open(self.name+'_log.txt', 'a')

         for i in data:
             file.write(str(i))
             file.write('|')
         file.write('\n')

         file.close()


    def update_parameters(self, Kp, Ti):
        self.Kp = Kp # Proporsjonal forsterkning
        self.Ti = Ti # Integraltid
    
    def update_value(self, value):
        print("updating value")
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
        u_p = round(u_p,2)
        self.u_p = u_p

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
        if self.mode == 'Auto':
            self.get_sample_time()
            self.get_error()

            # Kalkuler proporsjonal-, integralbidraget til pådraget.
            self.proportional()
            self.integral()
            u_tot = self.u_p + self.u_i

            # Anti windup:
            if u_tot > 100.0:
                self.set_u_tot(100.0)
            elif u_tot < 0.0:
                self.set_u_tot(0.0)
            else:
                self.set_u_tot(round(u_tot, 2))

            results = [ctime(), self.value, self.setpoint, self.u_tot, self.u_p, self.u_i, self.Kp, self.Ti]

            # Logg resulateter hvis dette er aktivert (default = FALSE)
            if self.log_results:
                self.writer(results)

    # Duty cycle i minutter
    def actuationControl(self):
        dutycycle = None
        actuation = None

        while(self.run_actuation == True):

            if not self.lock.acquire(False):
                print("Failed to unlock the Lock")
            else:
                try:
                    print("Lock acquired")
                    dutycycle = self.dutycycle*60 # Konverterer til sekunder
                    actuation = self.u_tot

                finally:
                    self.lock.release()
                    print("Lock released")

                    t_on = (actuation/100)*dutycycle
                    t_off = dutycycle - t_on

                    try:
                        if(t_on != 0):
                            # Skru varmekabel på
                            self.activate_func(self.name)
                            print("on - {}s".format(t_on))
                    except:
                        print("could not activate heattrace")
                        print(sys.exc_info()[0])
                        sleep(5)
                    sleep(t_on)

                    try:
                        if(t_off != 0):
                            # Skru av varmekabel
                            self.deactivate_func(self.name)
                            print("off - {}s".format(t_off))
                    except:
                        print("could not deactivate heattrace")
                        print(sys.exc_info()[0])
                        sleep(5)
                    sleep(t_off)


    def set_dutycycle(self, dutycycle):
        self.lock.acquire()
        try:
            self.dutycycle = dutycycle
        finally:
            self.lock.release()

    def set_u_tot(self, u_tot):
        self.lock.acquire()
        try:
            self.u_tot = u_tot
        finally:
            self.lock.release()

    def change_mode(self, mode, actuation=0.0):
        if mode == 'Auto':
            self.bumpless(actuation)
            self.mode = 'Auto'
        elif mode == 'Manual':
            self.u_tot = actuation
            self.mode = 'Manual'
        else:
            print("Invalid controller mode ...")

    def stop(self):
        self.run_actuation = False

    def start(self):
        self.run_actuation = True


# def change_value(reg):
#     while(True):
#         command = input("")
#         reg.update_value(float(command))



# prompt  = Thread(target=change_value, args=(reg_1,))
# prompt.start()

#ac = Thread(target=actuationControl)
#ac.start()
