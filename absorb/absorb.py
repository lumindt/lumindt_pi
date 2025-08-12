from utils.omega import FMA5508A
from utils.sensors import ADS1115, megaTC
import csv
import time
import threading
import busio
import board


FC=FMA5508A(addr=0x4B)
ads=ADS1115()
ads1=ADS1115(addr=0x49)

SMLPM2GPS=1.5e-6
accumulated_flow = 0.0

spi=busio.SPI(clock=board.SCLK,MISO=board.MISO)
while not spi.try_lock():
    pass
spi.configure(baudrate=100000,phase=0,polarity=0)
spi.unlock()

extraTC=megaTC(spi_bus=spi)


def _accumulator():
    global accumulated_flow
    while True:
        t_start=time.time()
        time.sleep(0.0001)
        with _thread_lock:
            f=FC.flow()[0] * SMLPM2GPS
            accumulated_flow += f*(time.time()-t_start)


_flow_thread=threading.Thread(target=_accumulator,daemon=True)
_thread_lock=threading.Lock()
_flow_thread.start()

file='outputs/absorb_first_test.csv'

with open(file, 'w', newline='') as f:
    writer=csv.writer(f)
    writer.writerow([
        'Time',
        'Surface Temp',
        'T_R0_X0',
        'T_R0_X1',
        'T_R0.5_X1',
        'T_R1_X1',
        'T_R1.5_X1',
        'T_R0_X2',
        'Vessel Pressure',
        'Reg Pressure',
        'Flow Mass Rate',
        'Flow Setpoint',
        'Flow Total Mass',
    ])
    writer.writerow([
        's',
        'C',
        'C',
        'C',
        'C',
        'C',
        'C',
        'C',
        'barG',
        'barG',
        'g/s',
        'mL',
        'g',
    ])
    t_start=time.time()
    v_setpoint = 0.0
    FC.set_flow(v_setpoint)

    while True:
        try:
            t_now=time.time()
            v_pres=ads.pressure(2)
            surf_temp=ads.temperature(3)
            T_R0_X0 = extraTC.temp(1)[1]
            T_R0_X1 = ads1.temperature(1)
            T_R05_X1 = ads1.temperature(0)
            T_R1_X1 = extraTC.temp(2)[1]
            T_R15_X1 = extraTC.temp(0)[1]
            T_R0_X2 = ads1.temperature(3)
            reg_pres=ads1.pressure(2)

            with _thread_lock:
                v_flow=FC.flow()[0] * SMLPM2GPS
                total_flow=accumulated_flow
            
            writer.writerow([
                t_now-t_start,
                surf_temp,
                T_R0_X0,
                T_R0_X1,
                T_R05_X1,
                T_R1_X1,
                T_R15_X1,
                T_R0_X2,
                v_pres,
                reg_pres,
                v_flow,
                v_setpoint,
                total_flow
            ])

            string=(
                f'{"":-^30}\n'
                f'Time:         {t_now-t_start:0.2f}\n'
                f'Surface Temp: {surf_temp:0.2f} C\n'
                f'Vessel Pres:  {v_pres:0.2f} barG\n'
                f'Reg Pres      {reg_pres:0.2f} barG\n'
                f'Flow:         {v_flow:0.6f} g/s\n'
                f'Setpoint:     {v_setpoint:0.2f} mL\n'
                f'Total Flow:   {total_flow:0.6f} g\n'
                )
            print(string)
            while time.time()-t_now<2:
                pass
        except KeyboardInterrupt:
            try:
                cmd_string=(
                    f'\n1 -> New Omega Setpoint Flow\n'
                    f'2 -> Reset Omega Accumulation\n'
                    f'Any other number will continue\n'
                    f'Press ENTER to end script\n'
                )
                cmd=float(input(cmd_string))
                if cmd==1:
                    v_setpoint=float(input('Enter new setpoint flow (mL): '))
                    FC.set_flow(v_setpoint)
                elif cmd==2:
                    accumulated_flow = 0
                else:
                    continue
            except:
                print('...Ending...')
                break
        except Exception as e:
            print(e)
            break
 