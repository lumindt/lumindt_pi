from utils.sensors import ADS1115
# from utils.kiln import Controller as KilnController
from utils.alicat import Controller as FlowController
import time
import csv

# kiln=KilnController()

FC=FlowController()
FC.gas='H2'
FC.ramp=0

ads = ADS1115(0x48)
ads1 = ADS1115(0x49)

file='outputs/ZhenAn_B25V1T2_Hot_Desorb.csv'
with open(file, 'w', newline='') as f:
    writer=csv.writer(f)
    writer.writerow([
        'Time (s)',
        # 'Kiln Status',
        # 'Kiln Paused',
        # 'Kiln Temp (C)',
        'Vessel Temp (C)',
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
        # 'bool',
        # 'bool',
        # 'C',
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
    while True:
        try:
            t_now=time.time()
            v_pres=ads1.pressure(2)
            # k_temp=ads.temperature(1)
            v_temp=ads.temperature(0)
            FCdata=FC.poll()
            # kiln.update(k_temp)
            writer.writerow([
                t_now-t_start,
                # kiln.status,
                # kiln.pause,
                # k_temp,
                v_temp,
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
                f'Time:         {t_now-t_start:0.2f}\n'
                # f'Kiln Temp:    {k_temp:0.2f} C (CONTROL VARIABLE)\n'
                f'Vessel Temp:  {v_temp:0.2f} C\n'
                f'Vessel Pres:  {v_pres:0.2f} barG\n'
                # f'Heat On:      {kiln.status}\n'
                # f'Kiln Paused:  {kiln.pause}\n'
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
                    f'\n0 -> Kiln Off\n'
                    f'1 -> Kiln On\n'
                    f'2 -> New Kiln Setpoint Temp\n'
                    f'3 -> New Kiln Temp Bound\n'
                    f'4 -> New Alicat Setpoint Flow\n'
                    f'5 -> Reset Alicat Accumulation\n'
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
                elif cmd==4:
                    new=float(input('New Setpoint: '))
                    FC.setpoint = new
                elif cmd==5:
                    FC.totalizer_reset()
                else:
                    continue
            except:
                print('...Ending...')
                print(f'TMFs: {len(FC.mass_flow_totals)}')
                break
        except Exception as e:
            print(e)
            break
    FC.setpoint=0
    # kiln.stop()