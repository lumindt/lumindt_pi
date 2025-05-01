from sensors import ADS1115
import threading
import gpiozero
import time

class kiln:

    def __init__(self):
        self.trigger=gpiozero.OutputDevice(pin=4) # Confirm pin number
        self.trigger.off()

        self.control_temp=100
        self.control_bound=5
        self.control_lock=threading.Lock()
        self.control_pause=True
        self.control_stop=False
        self.control_thread=threading.Thread(target=self.run,daemon=True)
        self.control_thread.start()

    def run(self):
        while not self.control_stop:
            with self.control_lock:
                if not self.control_pause:
                    lo=self.control_temp-self.control_bound
                    hi=self.control_temp+self.control_bound
                    if self.internal_temp>hi:
                        self.trigger.off()
                    elif self.internal_temp<lo:
                        self.trigger.on()
                else:
                    self.trigger.off()
            time.sleep(0.1)

    def update(self,active_temp):
        with self.control_lock:
            self.internal_temp=active_temp
                    
    @property
    def setpoint(self):
        with self.control_lock:
            return self.control_temp

    @setpoint.setter
    def setpoint(self,value):
        with self.control_lock:
            self.control_temp=min([value,500])

    @property
    def bound(self):
        with self.control_lock:
            return self.control_bound

    @bound.setter
    def bound(self,value):
        with self.control_lock:
            self.control_bound=value

    @property
    def pause(self):
        with self.control_lock:
            return self.control_pause
        
    @pause.setter
    def pause(self,value):
        with self.control_lock:
            self.control_pause=bool(value)

    @property
    def status(self):
        with self.control_lock:
            return self.trigger.value

    def stop(self):
        self.control_stop=True
        self.trigger.off()
        self.trigger.close()

if __name__=='__main__':
    
    kiln=kiln()
    kiln.pause=True
    kiln.temp=25
    kiln.bound=3

    ads=ADS1115()

    t_start=time.time()
    while True:
        try:
            t_now=time.time()
            kiln.update(ads.temperature(1,offset=1.25))
            string=(
                f'time:     {t_now-t_start:0.2f}\n'
                f'pres0:    {ads.pressure(0):0.2f}\n'
                f'temp1:    {ads.temperature(1,offset=1.25):0.2f} (CONTROL VARIABLE)\n'
                f'temp2:    {ads.temperature(2,offset=1.25):0.2f}\n'
                f'status:   {kiln.status}\n'
                f'pause:    {kiln.pause}\n'
                )
            print(string)
            while time.time()-t_now<1:
                pass
        except KeyboardInterrupt:
            try:
                cmd_string=(
                    '\n'
                    f'0 -> Kiln Off\n'
                    f'1 -> Kiln On\n'
                    f'2 -> New Kiln Setpoint Temp\n'
                    f'3 -> New Kiln Temp Bound\n'
                    f'Any other number will continue\n'
                    f'Press ENTER to end script\n'
                )
                cmd=float(input(cmd_string))
                if cmd==0:
                    kiln.pause = True
                elif cmd==1:
                    kiln.pause = False
                elif cmd==2:
                    new=float(input('New Setpoint: '))
                    kiln.setpoint = new
                elif cmd==3:
                    new=float(input('New Bound: '))
                    kiln.bound = new
                else:
                    continue
            except:
                print('Ending')
                kiln.stop()
                break
        except Exception as e:
            print(e)
            kiln.stop()
            break


            
    

        