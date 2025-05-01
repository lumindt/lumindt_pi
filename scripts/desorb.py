from pi_utils.sensors import ADS1115
from pi_utils.kiln import Controller as KilnController
from pi_utils.alicat import Controller as FlowController

import csv

kiln=KilnController()
FC=FlowController()
adc=ADS1115()

file=''
with open(file, 'w', newline='') as f:
    writer=csv.writer(f)
    writer.writerow([
        'Time',

    ])
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