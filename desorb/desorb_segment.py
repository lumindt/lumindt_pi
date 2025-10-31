from utils.sensors import ADS1115, megaTC
from utils.alicat import Controller as FlowController
import busio
import board
import time
import csv

segments=[[0.000100,4],[0.000055,-1]]

FC=FlowController()
FC.gas='H2'
FC.ramp=0

# spi=busio.SPI(clock=board.SCLK,MISO=board.MISO)
# while not spi.try_lock():
#     pass
# spi.configure(baudrate=100000,phase=0,polarity=0)
# spi.unlock()

ads0=ADS1115(addr=0x48)
ads1=ADS1115(addr=0x49)

file='outputs/InnerMongolia_HES_26_T2_LongDesorb.csv'
with open(file, 'w', newline='') as f:
    writer=csv.writer(f)
    writer.writerow([
        'Time',
        'T_Z0_R0',
        'T_Z1_R0',
        'T_Z2_R0',
        'T_Z1_R1',
        'T_Z1_R2',
        'T_Z1_R3',
        'Vessel Pressure',
        'Flow Pressure',
        'Flow Temperature',
        'Flow Volume Rate',
        'Flow Mass Rate',
        'Flow Setpoint',
        'Flow Total Mass',
        'Flow Error Codes',
    ])
    FCdata=FC.poll()
    # write row of units:
    writer.writerow([
        's',
        'C',
        'C',
        'C',
        'C',
        'C',
        'C',
        'barG',
        FCdata['P'][1],  # Pressure unit
        FCdata['T'][1],  # Temperature unit
        FCdata['V'][1],  # Volumetric flow unit
        FCdata['M'][1],  # Mass flow unit
        FCdata['S'][1],  # Mass flow setpoint unit
        FCdata['A'][1],  # Accumulated mass unit
        'error codes'
    ])
    FC.totalizer_reset(1)
    t_start=time.time()
    m_setpoint = 0.0
    segment = -1
    FC.setpoint=m_setpoint
    while True:
        try:
            t_now=time.time()
            v_pres=ads1.pressure(2)
            T_Z0_R0 = ads0.temperature(0)
            T_Z1_R0 = ads0.temperature(1)
            T_Z2_R0 = ads0.temperature(3)
            T_Z1_R1 = ads1.temperature(0)
            T_Z1_R2 = ads1.temperature(1)
            T_Z1_R3 = ads1.temperature(3)
            FCdata=FC.poll()

            if segment!=-1 and v_pres <= segments[segment][1]:
                segment += 1
                FC.setpoint=segments[segment][0]
                print(segments[segment])

            writer.writerow([
                t_now-t_start,
                T_Z0_R0,
                T_Z1_R0,
                T_Z2_R0,
                T_Z1_R1,
                T_Z1_R2,
                T_Z1_R3,
                v_pres,
                FCdata['P'][0],
                FCdata['T'][0],
                FCdata['V'][0],
                FCdata['M'][0],
                FCdata['S'][0],
                FCdata['A'][0],
                FCdata['E'],
            ])
            string=(
                f'{"":-^30}\n'
                f'Time:         {(t_now-t_start):0.2f}\n\n'
                f'Z2:           {T_Z2_R0:^10.2f}{"":<10}{"":<10}{"":<9}|\n'
                f'Z1:           {T_Z1_R0:^10.2f}{T_Z1_R1:^10.2f}{T_Z1_R2:^10.2f}{T_Z1_R3:^9.2f}\n'
                f'Z0:           {T_Z0_R0:^10.2f}{"":<10}{"":<10}{"":<9}|\n\n'
                f'Vessel Pres:  {v_pres:0.2f} barG\n'
                f'FC Pres:      {FCdata["P"][0]:0.2f} {FCdata["P"][1]}\n'
                f'FC Temp:      {FCdata["T"][0]:0.2f} {FCdata["T"][1]}\n'
                f'FC V Flow:    {FCdata["V"][0]:0.2f} {FCdata["V"][1]}\n'
                f'FC M Flow:    {FCdata["M"][0]:0.6f} {FCdata["M"][1]}\n'
                f'FC Setpoint:  {FCdata["S"][0]:0.6f} {FCdata["S"][1]}\n'
                f'FC Total:     {FCdata["A"][0]:0.6f} {FCdata["A"][1]}\n'
                f'FC Errors:    {FCdata["E"]}\n'
                )
            print(string)
            while time.time()-t_now<2:
                pass
        except KeyboardInterrupt:
            try:
                cmd_string=(
                    f'\n0 -> Start\n'
                    f'1 -> Reset Alicat Accumulation\n'
                    f'Any other number will continue\n'
                    f'Press ENTER to end script\n'
                )
                cmd=float(input(cmd_string))
                if cmd==0:
                    segment = 0
                    m_setpoint = segments[segment][0]
                    print(m_setpoint)
                    FC.setpoint=m_setpoint
                elif cmd==1:
                    FC.totalizer_reset()
                else:
                    continue
            except:
                print('...Ending...')
                break
        except Exception as e:
            print(e)
            break
    FC.setpoint=0