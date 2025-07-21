from utils.sensors import ADS1115, EMA, megaTC
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

def _print_data(state):
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

    writer.writerow([
        t_now-t_start,
        state,
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
    
    string=(
        f'{"":-^30}\n'
        f'Time:         {t_now-t_start:0.2f}\n'
        f'State:        {state}\n'
        f'Kiln Temp:    {k_temp:0.2f} C (CONTROL VARIABLE)\n'
        f'Vessel Temp:  {surf_temp:0.2f} C\n'
        f'Vessel Pres:  {v_pres:0.2f} barG\n'
        f'Heat On:      {kiln.status}\n'
        f'Kiln Paused:  {kiln.pause}\n'
        f'FC Pres:      {FCdata["P"][0]:0.2f} {FCdata["P"][1]}\n'
        f'FC Temp:      {FCdata["T"][0]:0.2f} {FCdata["T"][1]}\n'
        f'FC V Flow:    {FCdata["V"][0]:0.2f} {FCdata["V"][1]}\n'
        f'FC M Flow:    {FCdata["M"][0]:0.6f} {FCdata["M"][1]}\n'
        f'FC Setpoint:  {FCdata["S"][0]:0.6f} {FCdata["S"][1]}\n'
        f'FC Total:     {FCdata["A"][0]:0.6f} {FCdata["A"][1]}\n'
        f'FC Errors:    {FCdata["E"]}\n\n'
        f'Stop Mass:    {M_stop} g\n'
        )
    print(string)
    

def controlled_desorb(stop_point, setpoint):
    kiln.pause = True
    FCdata = FC.poll()
    total_mass = FCdata['A'][0]
    FC.setpoint = setpoint

    while total_mass < stop_point:
        _print_data(state="Controlled Desorb")
        total_mass = FC.poll()['A'][0]
        time.sleep(1)

    REFERENCE_T = extraTC.temp(1)[1]
    CURRENT_T = 0
    BUFFER = 2
    FC.setpoint = 0

    while CURRENT_T < (REFERENCE_T + BUFFER):
        _print_data(state="Equilization Period")
        print(f'Reference temp: {REFERENCE_T}, current temp {CURRENT_T}')
        time.sleep(1)
        CURRENT_T = extraTC.temp(1)[1]
    pass

def fast_return(stop_point):
    kiln.pause = False
    kiln.setpoint = 50
    FC.setpoint = 0.0048
    
    FCdata = FC.poll()
    total_mass = FCdata['A'][0]
    print(f"Total mass {total_mass} stop point {stop_point}")
    try: 
        while total_mass < stop_point:
            _print_data(state='Fast Desorb')
            surf_temp = ads0.temperature(3)
            k_temp=ads0.temperature(1)
            kiln.update(k_temp)
            total_mass = FC.poll()['A'][0]

            if surf_temp > 20:
                kiln.pause = True
        
    except Exception as e:
        print(e)
    FC.setpoint = 0

    while surf_temp < 20:
        time.sleep(1)
        _print_data(state="Awaiting kiln pause")  
        surf_temp = ads0.temperature(3) 

    kiln.pause = True
    pass

def await_steady_state():
    steady_count = 0
    sample_interval = 2

    prev_t = extraTC.temp(1)[1]

    while True:
        time.sleep(sample_interval)
        _print_data(state="Awaiting Steady State")
        curr_t = extraTC.temp(1)[1]
        dp_dt = (curr_t - prev_t) / sample_interval

        if abs(dp_dt) < 0.05:
            steady_count += 1
            if steady_count >= 5:
                return curr_t
        else:
            steady_count = 0

        prev_t = curr_t


FILE='outputs/Molina_B2V1T4_Qgen_4.csv'

with open(FILE, 'w', newline='') as f:
    writer=csv.writer(f)
    writer.writerow([
        'time',
        'state',
        'kiln status',
        'Kiln Paused',
        'Kiln Temp',
        'Surface Temp',
        'T_R0_X0',
        'T_R0_X1',
        'T_R0.5_X1',
        'T_R1_X1',
        'T_R1.5_X1',
        'T_R0_X2',
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
    writer.writerow([
        's',
        'string'
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
    t_start=time.time()

    M_stop=0
    F_stop=0

    while True:
        try:
           _print_data(state="Standby")
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
                        '\nEnter the total mass (g) to stop at: \n'
                        '(Refer to test plan)\n'
                    )
                    M_stop=float(input(stop_string))
                    stop_string=(
                        '\nEnter the total mass (g) to fast desorb to: \n'
                        '(Refer to test plan)\n'
                    )
                    F_stop=float(input(stop_string))
                    flow_string=(
                        '\nEnter the flow rate (g/s) to set: \n'
                        '(Typical: 0.00167 g/s)\n'
                    )
                    flow_setpoint=float(input(flow_string))
                    FC.setpoint = flow_setpoint
                    try:
                        # controlled_desorb(M_stop, flow_setpoint)
                        fast_return(F_stop)
                        await_steady_state()
                        print('cycle finished')
                    except:
                        pass
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