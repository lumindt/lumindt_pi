from utils.sensors import ADS1115
from utils.kiln import Controller as KilnController
from utils.alicat import Controller as FlowController
import time
import csv

kiln=KilnController()
#testing github - colin
FC=FlowController()
FC.gas='H2'
FC.ramp=0

ads=ADS1115()

pulse_max=15
pulse=0
pulse_flow=0

file='outputs/test.csv'
with open(file, 'w', newline='') as f:
    writer=csv.writer(f)
    writer.writerow([
        'Time (s)',
        'Kiln Status',
        'Kiln Paused',
        'Kiln Temp (C)',
        'Vessel Temp (C)',
        'Vessel Pressure (barG)',
        'Flow Pressure (barA)',
        'Flow Temp (C)',
        'Flow Volumetric Rate (SLPM)',
        'Flow Mass Rate (g/s)',
        'Flow Setpoint (g/s)',
        'Flow Total Mass (g)',
        'Flow Averaged Rate (g/s)',
        'Flow Errors',
    ])
    FC.totalizer_reset()
    t_start=time.time()
    t_ref=t_start
    while True:
        try:
            t_now=time.time()
            v_pres=ads.pressure(0)
            k_temp=ads.temperature(1,offset=1.25)
            v_temp=ads.temperature(2,offset=1.25)
            FCdata=FC.poll()
            avgflow=FCdata['A']/(t_now-t_ref)

            if pulse==pulse_max:
                FC.setpoint=pulse_flow
            kiln.update(k_temp)
            
            writer.writerow([
                t_now-t_start,
                kiln.status,
                kiln.pause,
                k_temp,
                v_temp,
                v_pres,
                FCdata['P'],
                FCdata['T'],
                FCdata['V'],
                FCdata['M'],
                FCdata['S'],
                FCdata['A'],
                avgflow,
                FCdata['E']
            ])
            string=(
                f'{"":-^30}\n'
                f'Time:         {t_now-t_start:0.2f}\n'
                f'Kiln Temp:    {k_temp:0.2f} C (CONTROL VARIABLE)\n'
                f'Vessel Temp:  {v_temp:0.2f} C\n'
                f'Vessel Pres:  {v_pres:0.2f} barG\n'
                f'Heat On:      {kiln.status}\n'
                f'Kiln Paused:  {kiln.pause}\n'
                f'FC Pres:      {FCdata["P"]:0.2f} barA\n'
                f'FC Temp:      {FCdata["T"]:0.2f} C\n'
                f'FC V Flow:    {FCdata["V"]:0.2f} SLPM\n'
                f'FC M Flow:    {FCdata["M"]:0.6f} g/s\n'
                f'FC Setpoint:  {FCdata["S"]:0.6f} g/s\n'
                f'FC Total:     {FCdata["A"]:0.6f} grams\n'
                f'FC Avg Flow:  {avgflow:0.6f} g/s\n'
                f'FC Errors:    {FCdata["E"]}\n'
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
                    f'4 -> New Alicat setpoint flow\n'
                    f'5 -> Reset Alicat accumulation, avg flow, and errors\n'
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
                elif cmd==4:
                    new=float(input('New setpoint: '))
                    pulse_flow = new
                elif cmd==5:
                    FC.totalizer_reset()
                    t_ref=time.time()
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