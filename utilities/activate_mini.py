from utils.sensors import ADS1115
import time
import csv

ads1 = ADS1115(0x48)
ads=ADS1115(0x49)

file='ZhenAn_B25V1T1_Activate_Mini.csv'
with open(file, 'w', newline='') as f:
    writer=csv.writer(f)
    writer.writerow([
        'Time (s)',
        'Vessel Temp (C)',
        'Vessel Pressure (barG)',
    ])
    t_start=time.time()
    t_ref=t_start
    while True:
        try:
            t_now=time.time()
            v_pres=ads.pressure(pin=2, max_bar=68.95)
            v_temp=ads1.temperature(0)

            writer.writerow([
                t_now-t_start,
                v_temp,
                v_pres
            ])
            string=(
                f'{"":-^30}\n'
                f'Time:         {t_now-t_start:0.2f}\n'
                f'Vessel Temp:  {v_temp:0.2f} C\n'
                f'Vessel Pres:  {v_pres:0.2f} barG\n'
                )
            print(string)
            while time.time()-t_now<2:
                pass
        except KeyboardInterrupt:
            try:
                cmd_string=(
                    f'Any other number will continue\n'
                    f'Press ENTER to end script\n'
                )
                cmd=float(input(cmd_string))
                continue
            except:
                print('...Ending...')
                break
        except Exception as e:
            print(e)
            break
