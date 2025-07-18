from utils.sensors import ADS1115, megaTC
from utils.kiln import Controller as KilnController
import busio
import board
import time
import csv

kiln=KilnController()

spi=busio.SPI(clock=board.SCLK,MISO=board.MISO)
while not spi.try_lock():
    pass
spi.configure(baudrate=100000,phase=0,polarity=0)
spi.unlock()

ads0=ADS1115(addr=0x48)
ads1=ADS1115(addr=0x49)
extraTC=megaTC(spi_bus=spi)

pulse_max=30
pulse=0
pulse_flow=0

file='outputs/Molina_B2V1T1_Instrumentation_Activation.csv'
with open(file, 'w', newline='') as f:
    writer=csv.writer(f)
    writer.writerow([
        'Time (s)',
        'Kiln Status',
        'Kiln Paused',
        'Kiln Temp (C)',
        'Surface Temp (C)',
        'T_R0_X0 (C)',
        'T_R0_X1 (C)',
        'T_R0.5_X1 (C)',
        'T_R1_X1 (C)',
        'T_R1.5_X1 (C)',
        'T_R0_X2 (C)',
        'Vessel Pressure (barG)',
    ])
    t_start=time.time()
    t_ref=t_start
    while True:
        try:
            t_now=time.time()
            v_pres=ads0.pressure(2)
            k_temp=ads0.temperature(1)
            surf_temp=ads0.temperature(3)
            T_R0_X0 = extraTC.temp(1)[1]
            T_R0_X1 = ads1.temperature(1)
            T_R05_X1 = ads1.temperature(0)
            T_R1_X1 = extraTC.temp(2)[1]
            T_R15_X1 = extraTC.temp(0)[1]
            T_R0_X2 = ads1.temperature(3)


            kiln.update(k_temp)
            
            writer.writerow([
                t_now-t_start,
                kiln.status,
                kiln.pause,
                k_temp,
                surf_temp,
                T_R0_X0,
                T_R0_X1,
                T_R05_X1,
                T_R1_X1,
                T_R15_X1,
                T_R0_X2,
                v_pres
            ])
            string=(
                f'{"":-^30}\n'
                f'Time:         {t_now-t_start:0.2f}\n'
                f'Kiln Temp:    {k_temp:0.2f} C (CONTROL VARIABLE)\n'
                f'Surface Temp:  {surf_temp:0.2f} C\n'
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