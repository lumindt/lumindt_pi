from utils.sensors import ADS1115, megaTC
from utils.kiln import Controller as KilnController
from utils.alicat import Controller as FlowController
import busio
import board
import time
import csv

kiln=KilnController()
kiln.setpoint=100
kiln.bound=5

spi=busio.SPI(clock=board.SCLK,MISO=board.MISO)
while not spi.try_lock():
    pass
spi.configure(baudrate=100000,phase=0,polarity=0)
spi.unlock()

ads0=ADS1115(addr=0x48)
ads1=ADS1115(addr=0x49)
extraTC=megaTC(spi_bus=spi)

FC=FlowController()
FC.gas='H2'
FC.ramp=0

ads=ADS1115()

file='outputs/qgen_test3.csv'
with open(file, 'w', newline='') as f:
    writer=csv.writer(f)
    writer.writerow([
        'Time',
        'Kiln Status',
        'Kiln Paused',
        'Kiln Temp',
        'Surface Temp',
        'T_Z0_R0',
        'T_Z1_R0',
        'T_Z2_R0',
        'T_Z1_R1',
        'T_Z1_R2',
        'T_Z1_R3',
        'Vessel Pressure',
        'Flow Pressure',
        'Flow Temp',
        'Flow Volumetric Rate',
        'Flow Mass Rate',
        'Flow Setpoint',
        'Flow Total Mass',
        'Flow Errors'
    ])
    FCdata=FC.poll()
    # write row of units:
    writer.writerow([
        's',
        'bool',
        'bool',
        'C',
        'C',
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
    FC.cancel_hold()
    print(FC.units)
    t_start=time.time()

    M_stop=0

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
            FCdata=FC.poll()
            if FCdata['A'][0] >= M_stop:
                FC.setpoint = 0
                kiln.pause = True
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
                v_pres,
                FCdata['P'][0],
                FCdata['T'][0],
                FCdata['V'][0],
                FCdata['M'][0],
                FCdata['S'][0],
                FCdata['A'][0],
                FCdata['E']
            ])
            print('1')
            string=(
                f'{"":-^30}\n'
                f'Time:         {t_now-t_start:0.2f}\n'
                f'Kiln Temp:    {k_temp:0.2f} C (CONTROL VARIABLE)\n'
                f'Vessel Temp:  {surf_temp:0.2f} C\n'
                f'Vessel Pres:  {v_pres:0.2f} barG\n'
                f'Heat On:      {kiln.status}\n'
                f'Kiln Paused:  {kiln.pause}\n'
                f'FC Pres:      {FCdata["P"][0]:0.2f} barA\n'
                f'FC Temp:      {FCdata["T"][0]:0.2f} C\n'
                f'FC V Flow:    {FCdata["V"][0]:0.2f} SLPM\n'
                f'FC M Flow:    {FCdata["M"][0]:0.6f} g/s\n'
                f'FC Setpoint:  {FCdata["S"][0]:0.6f} g/s\n'
                f'FC Total:     {FCdata["A"][0]:0.6f} grams\n'
                f'FC Errors:    {FCdata["E"]}\n'
                )
            print(string)
            while time.time()-t_now<2:
                pass
        except KeyboardInterrupt:
            try:
                cmd_string=(
                    f'\n0 -> Kiln Off\n'
                    f'1 -> Kiln On\n'
                    f'2 -> Kiln Tune\n'
                    f'3 -> New Cycle\n'
                    f'Any other number will continue\n'
                    f'Press ENTER to end script\n'
                )
                cmd=float(input(cmd_string))
                if cmd==0:
                    kiln.pause = True
                elif cmd==1:
                    kiln.pause = False
                elif cmd==2:
                    temp_string=(
                        '\nEnter the kiln setpoint temperature (C): \n'
                        '(Typical: 100 C)\n'
                    )
                    kiln.setpoint=float(input(temp_string))
                    bound_string=(
                        '\nEnter the kiln temperature bound (C): \n'
                        '(Typical: 5 C)\n'
                    )
                    kiln.bound=float(input(bound_string))
                elif cmd==3:
                    stop_string=(
                        '\nEnter the mass (g) to stop at: \n'
                        '(Refer to test plan)\n'
                    )
                    M_stop=float(input(stop_string))
                    flow_string=(
                        '\nEnter the flow rate (g/s) to set: \n'
                        '(Typical: 0.00167 g/s)\n'
                    )
                    FC.setpoint=float(input(flow_string))
                    time.sleep(0.2)
                    print(FC.setpoint)
                else:
                    continue
            except:
                print('...Ending...')
                break
        except Exception as e:
            print(e)
            break
    FC.setpoint=0
    kiln.stop()