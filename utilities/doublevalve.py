import gpiozero
import time
import csv
from utils.sensors import ADS1115

VI=gpiozero.OutputDevice(pin=17)
VO=gpiozero.OutputDevice(pin=27)

file='outputs/BIGBOI_HES06.csv'
with open(file, 'w', newline='') as f:
    writer=csv.writer(f)
    writer.writerow([
        'Time (s)',
        'Valve In',
        'Valve OUT',
        'Vessel Pressure (barG)',
        'Tank Pressure (barG)',
    ])
    t_start=time.time()
    while True:
        try:
            t_now=time.time()-t_start
            vi_status=VI.value
            vo_status=VO.value
            p_v=ADS1115().pressure(2)
            p_t=ADS1115(addr=0x49).pressure(2)

            writer.writerow([
                t_now-t_start,
                vi_status,
                vo_status,
                p_v,
                p_t
            ])

            string=(
                f'{"":-^30}\n'
                f'Time:         {t_now:0.2f}\n'
                f'VI:           {vi_status}\n'
                f'VO:           {vo_status}\n'
                f'Vessel Pres:  {p_v:0.2f} barG\n'
                f'Tank Pres:    {p_t:0.2f} barG\n'
                )
            print(string)
            while time.time()-t_now-t_start<1:
                pass
        except KeyboardInterrupt:
            cmdstring=(
                f'\n\n0 -> Close\n'
                f'1 -> Fill\n'
                f'2 -> Purge\n'
                f'3 -> Continue\n'
            )
            print(cmdstring)
            cmd=input('Command: ')
            if cmd=='0':
                print('Closing')
                VI.off()
                VO.off()
            elif cmd=='1':
                print('Filling')
                VO.off()
                time.sleep(0.2)
                VI.on()
            elif cmd=='2':
                print('Purging')
                VI.off()
                time.sleep(0.2)
                VO.on()
            elif cmd=='3':
                print('Continuing')
                pass
            else:
                break
VI.close()
VO.close()
