<<<<<<< HEAD
from mqtt import activateHeatTrace, deactivateHeatTrace
=======
from mqtt import *
<<<<<<< HEAD
>>>>>>> 2c1f2d3265f0c9cbba3f847dce37d1d9cb064013
from threading import Timer, Thread, Lock
from time import time, ctime, sleep


<<<<<<< HEAD
class PI_controller:
=======
class PID_controller:
>>>>>>> 2c1f2d3265f0c9cbba3f847dce37d1d9cb064013

    def __init__(self, reg_name, mode="Auto", duty_cycle=1.0, log_results=False):

        self.name = reg_name
        self.log_results = log_results

<<<<<<< HEAD
        self.Kp = 0.0 # Proportional forsterkning
        self.Ti = 0.0 # Integraltid
        self.Ts = 0.0 # Samplingstid
=======
        self.Kp = 0.0 #proportional gain
        self.Ti = 0.0 #integral gain
        self.Ts = 0.0 #samplings time
>>>>>>> 2c1f2d3265f0c9cbba3f847dce37d1d9cb064013

        self.setpoint = 0
        self.error = 0

        self.u_p = 0
        self.u_i = 0
        self.u_tot = 0

<<<<<<< HEAD
        # Tilbakekoblingsverdi:
=======
        # feedback value:
>>>>>>> 2c1f2d3265f0c9cbba3f847dce37d1d9cb064013
        self.value = 0
        self.value_prev = 0

        self.time_now = time()
        self.time_prev = 0

        self.dutycycle = duty_cycle # min
<<<<<<< HEAD
        self.lock = Lock() # Lock for u_tot and dutycycle
=======
        self.lock = Lock() # lock for u_tot and dutycycle
>>>>>>> 2c1f2d3265f0c9cbba3f847dce37d1d9cb064013

        self.mode = mode
        self.run_thread = True

        self.actuation_control = Thread(target=self.actuationControl)
        self.actuation_control.start()

    def get_reg_name(self):
        return self.name

    # Write a log with results from the regulator
    def writer(self, data):
         file = open(self.name+'_log.txt', 'a')

         for i in data:
             file.write(str(i))
             file.write('|')
         file.write('\n')

         file.close()


    def update_parameters(self, Kp, Ti):
<<<<<<< HEAD
        self.Kp = Kp # Proportional forsterkning
        self.Ti = Ti # Integraltid
=======
        self.Kp = Kp #proportional gain
        self.Ti = Ti #integral gain
>>>>>>> 2c1f2d3265f0c9cbba3f847dce37d1d9cb064013
    
    def update_value(self, value):
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

<<<<<<< HEAD
    # Proporsjonalbidrag
=======
    # proportional part
>>>>>>> 2c1f2d3265f0c9cbba3f847dce37d1d9cb064013
    def proportional(self):
        u_p = self.Kp * self.error
        u_p = round(u_p,2)
        self.u_p = u_p

<<<<<<< HEAD
    # Intagralbidrag
=======
    # intagral part
>>>>>>> 2c1f2d3265f0c9cbba3f847dce37d1d9cb064013
    def integral(self):
        try:
            u_i = self.Kp * self.Ts / self.Ti * self.error + self.u_i
            self.u_i = round(u_i,2)

<<<<<<< HEAD
            # Anti windup:
=======
            # anti windup:
>>>>>>> 2c1f2d3265f0c9cbba3f847dce37d1d9cb064013
            if u_i > 100.0:
                self.u_i = 100.0
            elif u_i < 0.0:
                self.u_i = 0.0

        except ZeroDivisionError:
            self.u_i = 0.00

    def bumpless(self, u_tot):
<<<<<<< HEAD
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
=======
        # kjør denne hvis det byttes til regulatorstyring etter å ha brukt manuell pådrag
        # "reset" tida og bruk integralvirkning som det gamle pådraget
        self.u_i = u_tot
        self.get_sample_time()
            
    # calculate error
    def get_error(self):
        error = self.setpoint - self.value
        error = round(error,2)
        self.error = error

    def calculate_u_tot(self):
        if self.mode == "Auto":
            self.get_sample_time()
            self.get_error()

            #calculate proportional, integral and derivative "pådrag"
            self.proportional()
            self.integral()

            u_tot = self.u_p + self.u_i

            # anti windup:
>>>>>>> 2c1f2d3265f0c9cbba3f847dce37d1d9cb064013
            if u_tot > 100.0:
                self.set_u_tot(100.0)
            elif u_tot < 0.0:
                self.set_u_tot(0.0)
            else:
                self.set_u_tot(round(u_tot, 2))

            results = [ctime(), self.value, self.setpoint, self.u_tot, self.u_p, self.u_i, self.Kp, self.Ti]

<<<<<<< HEAD
            # Logg resulateter hvis dette er aktivert (default = FALSE)
            if self.log_results:
                self.writer(results)

    # Duty cycle i minutter
=======
            # log results if the optiion is on - default = FALSE
            if self.log_results:
                self.writer(results)

            #return results

    # duty cycle i minutter
>>>>>>> 2c1f2d3265f0c9cbba3f847dce37d1d9cb064013
    def actuationControl(self):
        dutycycle = None
        actuation = None

        while(self.run_thread == True):

            if not self.lock.acquire(False):
                print("Failed to unlock the Lock")
            else:
                try:
                    print("Lock acquired")
<<<<<<< HEAD
                    dutycycle = self.dutycycle*60 # Konverterer til sekunder
=======
                    dutycycle = self.dutycycle*60 # gjør om til sekund
>>>>>>> 2c1f2d3265f0c9cbba3f847dce37d1d9cb064013
                    actuation = self.u_tot

                finally:
                    self.lock.release()
                    print("Lock released")

                    t_on = (actuation/100)*dutycycle
                    t_off = dutycycle - t_on

                    # Skru varmekabel på
<<<<<<< HEAD
                    activateHeatTrace()
=======
                    #activateHeatTrace()
>>>>>>> 2c1f2d3265f0c9cbba3f847dce37d1d9cb064013
                    print("on - {}s".format(t_on))
                    sleep(t_on)

                    # Skru av varmekabel
<<<<<<< HEAD
                    deactivateHeatTrace()
=======
                    #deactivateHeatTrace()
>>>>>>> 2c1f2d3265f0c9cbba3f847dce37d1d9cb064013
                    print("off - {}s".format(t_off))
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
<<<<<<< HEAD
        if mode == 'Auto':
            self.bumpless(actuation)
            self.mode = 'Auto'
        elif mode == 'Manual':
            self.u_tot = actuation
            self.mode = 'Manual'
=======
        if mode == "Auto":
            self.bumpless(actuation)
            self.mode = "Auto"
        elif mode == "Manual":
            self.u_tot = actuation
            self.mode = "Manual"
>>>>>>> 2c1f2d3265f0c9cbba3f847dce37d1d9cb064013
        else:
            print("Invalid controller mode ...")

    def stop(self):
        self.run = False

    def start(self):
        self.run = True


<<<<<<< HEAD
# def change_value(reg):
#     while(True):
#         command = input("")
#         reg.update_value(float(command))

# reg_1 = PID_controller("regulator 1", duty_cycle=10.0/60)
# reg_1.set_dutycycle(10.0/60)
# reg_1.update_parameters(1.0, 1.0)
# reg_1.update_setpoint(2.0)

# prompt  = Thread(target=change_value, args=(reg_1,))
# prompt.start()

#ac = Thread(target=actuationControl)
#ac.start()
=======
def change_value(reg):
    while(True):
        command = input("")
        reg.update_value(float(command))

#reg_1 = PID_controller("regulator 1", duty_cycle=10.0/60)
#reg_1.set_dutycycle(10.0/60)
#reg_1.update_parameters(1.0, 1.0)
#reg_1.update_setpoint(2.0)
#
#prompt  = Thread(target=change_value, args=(reg_1,))
#prompt.start()

#ac = Thread(target=actuationControl)
#ac.start()
=======
from threading import Timer

def powerControl(actuation, dutycycle):
    while (regMode == High):
        # Skru varmekabel på
        activateHeatTrace()
        Timer(actuation/100 * dutycycle)
        # Skru av varmekabel
        deactivateHeatTrace()
        Timer((1 - actuation/100) * dutycycle)
>>>>>>> 8e056217dc3fd7426139aa2f7e60ee8c818d756b
>>>>>>> 2c1f2d3265f0c9cbba3f847dce37d1d9cb064013
