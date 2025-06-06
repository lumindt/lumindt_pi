from utils.sensors import ADS1115
from utils.kiln import Controller as KilnController
import time
import csv

kiln=KilnController()

ads=ADS1115()

pulse_max=30
pulse=0
pulse_flow=0

file='outputs/ZhenAn_B2V1T1_Activation.csv'
with open(file, 'w', newline='') as f:
    writer=csv.writer(f)
    writer.writerow([
        'Time (s)',
        'Kiln Status',
        'Kiln Paused',
        'Kiln Temp (C)',
        'Vessel Temp (C)',
        'Vessel Pressure (barG)',
    ])
    t_start=time.time()
    t_ref=t_start
    while True:
        try:
            t_now=time.time()
            v_pres=ads.pressure(2)
            k_temp=ads.temperature(1)
            v_temp=ads.temperature(3)


            kiln.update(k_temp)
            
            writer.writerow([
                t_now-t_start,
                kiln.status,
                kiln.pause,
                k_temp,
                v_temp,
                v_pres
            ])
            string=(
                f'{"":-^30}\n'
                f'Time:         {t_now-t_start:0.2f}\n'
                f'Kiln Temp:    {k_temp:0.2f} C (CONTROL VARIABLE)\n'
                f'Vessel Temp:  {v_temp:0.2f} C\n'
                f'Vessel Pres:  {v_pres:0.2f} barG\n'
                f'Heat On:      {kiln.status}\n'
                f'Kiln Paused:  {kiln.pause}\n'
                )
            print(string)
            while time.time()-t_now<2:
                pass
        except KeyboardInterrupt:
            try:
                cmd_string=(
                    f'\n0 -> Kiln off\n'
                    f'1 -> Kiln on\n'
                    f'2 -> New kiln setpoint temp\n'
                    f'3 -> New kiln temp bound\n'
                    f'Any other number will continue\n'
                    f'Press ENTER to end script\n'
                )
                cmd=float(input(cmd_string))
                if cmd==0:
                    kiln.pause = True
                elif cmd==1:
                    kiln.pause = False
                elif cmd==2:
                    new=float(input('New setpoint: '))
                    kiln.setpoint = new
                elif cmd==3:
                    new=float(input('New bound: '))
                    kiln.bound = new
                else:
                    continue
            except:
                print('...Ending...')
                break
        except Exception as e:
            print(e)
            break
    kiln.stop()