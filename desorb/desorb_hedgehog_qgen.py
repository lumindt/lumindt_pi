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
FC.set_conversion()

ads=ADS1115()

file='outputs/test.csv'
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
        'Flow Pressure (barA)',
        'Flow Temp (C)',
        'Flow Volumetric Rate (SLPM)',
        'Flow Mass Rate (g/s)',
        'Flow Setpoint (g/s)',
        'Flow Total Mass (g)',
        'Flow Errors'
    ])
    FC.totalizer_reset(1)
    FC.cancel_hold()
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
            if FCdata['E'] >= M_stop:
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
                FCdata['P'],
                FCdata['T'],
                FCdata['V'],
                FCdata['M'],
                FCdata['S'],
                FCdata['A'],
                FCdata['E']
            ])
            string=(
                f'{"":-^30}\n'
                f'Time:         {t_now-t_start:0.2f}\n'
                f'Kiln Temp:    {k_temp:0.2f} C (CONTROL VARIABLE)\n'
                f'Vessel Temp:  {surf_temp:0.2f} C\n'
                f'Vessel Pres:  {v_pres:0.2f} barG\n'
                f'Heat On:      {kiln.status}\n'
                f'Kiln Paused:  {kiln.pause}\n'
                f'FC Pres:      {FCdata["P"]:0.2f} barA\n'
                f'FC Temp:      {FCdata["T"]:0.2f} C\n'
                f'FC V Flow:    {FCdata["V"]:0.2f} SLPM\n'
                f'FC M Flow:    {FCdata["M"]:0.6f} g/s\n'
                f'FC Setpoint:  {FCdata["S"]:0.6f} g/s\n'
                f'FC Total:     {FCdata["A"]:0.6f} grams\n'
                f'FC Errors:    {FCdata["E"]}\n'
                )
            print(string)
            while time.time()-t_now<2:
                pass
        except KeyboardInterrupt:
            try:
                cmd_string=(
                    f'\n0 -> Pause Test (for emergencies)\n'
                    f'1 -> New Cycle\n'
                    f'Any other number will continue\n'
                    f'Press ENTER to end script\n'
                )
                cmd=float(input(cmd_string))
                if cmd==0:
                    kiln.pause = True
                    FC.setpoint = 0
                elif cmd==1:
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
                    kiln_string=(
                        '\nKiln On?\n'
                        '(0 -> Off | 1 -> On)\n'
                    )
                    kiln.pause = not bool(input(kiln_string))
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