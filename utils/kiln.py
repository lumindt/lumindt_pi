from utils.sensors import ADS1115
import threading
import gpiozero
import time

class Controller:

    # Next Steps:
        # Remove threading
        # Tie control to update function

    def __init__(self):
        self.trigger=gpiozero.OutputDevice(pin=23) # Confirm pin number
        self.trigger.off()

        self.control_temp=100
        self.control_bound=5 # Only a lower bound
        self.control_pause=True

    def update(self,active_temp):
        '''
        Run this function repeatedly in the script
        Pass the desired control temperature
        '''
        if not self.control_pause:
            lo=self.control_temp-self.control_bound
            hi=self.control_temp
            if active_temp>hi:
                self.trigger.off()
            elif active_temp<lo:
                self.trigger.on()
        else:
            self.trigger.off()

                    
    @property
    def setpoint(self):
        return self.control_temp

    @setpoint.setter
    def setpoint(self,value):
        self.control_temp=min([value,500])

    @property
    def bound(self):
        return self.control_bound

    @bound.setter
    def bound(self,value):
        self.control_bound=value

    @property
    def pause(self):
        return self.control_pause
        
    @pause.setter
    def pause(self,value):
        if value: self.trigger.off()
        self.control_pause=bool(value)

    @property
    def status(self):
        return bool(self.trigger.value)

    def stop(self):
        self.trigger.off()
        self.trigger.close()

if __name__=='__main__':
    
    kiln=Controller()
    kiln.setpoint=25
    kiln.bound=3

    ads=ADS1115()

    t_start=time.time()
    while True:
        try:
            t_now=time.time()
            k_temp=ads.temperature(1)
            v_temp=ads.temperature(3)
            v_pres=ads.pressure(2)
            kiln.update(k_temp)
            string=(
                f'time:     {t_now-t_start:0.2f}\n'
                f'pres0:    {v_pres:0.2f}\n'
                f'temp1:    {k_temp:0.2f} (CONTROL VARIABLE)\n'
                f'temp2:    {v_temp:0.2f}\n'
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


            
    

        