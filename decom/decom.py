import time
import csv
import gpiozero
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from utils.sensors import ADS1115
from adafruit_mcp4728 import MCP4728

i2c = busio.I2C(board.SCL,board.SDA)
ad0 = ADS1115(bus=i2c,addr=0x48)
ad1 = ADS1115(bus=i2c,addr=0x49)
ad2 = ADS1115(bus=i2c,addr=0x4B)
dac = MCP4728(i2c,address=0x60)


svi=gpiozero.OutputDevice(pin=17)
svo=gpiozero.OutputDevice(pin=27)

# Conversion of normalized value to flow in g/s
norm2flow=10*0.9926*1.427/60

def close():
    dac.channel_a.normalized_value=0
    svi.off()
    svo.off()

def end():
    close()
    print(f'Valve Status:\n\tIn:\t{svi.value}\n\tOut:\t{svo.value}')
    svi.close()
    svo.close()

file='outputs/test.csv'
with open(file, 'w', newline='') as f:
    writer=csv.writer(f)
    writer.writerow([
        'Time (s)',
        'Vessel Temp 1 (C)',
        'Vessel Temp 2 (C)',
        'Vessel Temp 3 (C)',
        'Vessel Temp 4 (C)',
        'Vessel Temp 5 (C)',
        'Vessel Temp 6 (C)',        
        'Vessel Pressure (barG)',
        'Commanded Flow (g/s)',
        'Command Check (g/s)',
        'Omega Flow Rate (g/s)',
        'Total Mass (g)',
        'Valve In',
        'Valve Out',
    ])
    close()
    flow_setpoint=0
    total=0
    change_flag=False
    t_start=time.time()
    t_prev=t_start
    while True:
        try:
            t_now=time.time()
            volts=ad2.voltage
            flow=volts[0]/5*norm2flow #if volts[0]/5>=0.005 else 0
            check=volts[1]/5*norm2flow
            total+=flow*(t_now-t_prev)
            if change_flag:
                dac.channel_a.normalized_value=sorted([0,flow_setpoint/norm2flow,1])[1]
                change_flag=False
            tc1=ad0.temperature(0)
            tc2=ad0.temperature(1)
            tc3=ad0.temperature(3)
            tc4=ad1.temperature(0)
            tc5=ad1.temperature(1)
            tc6=ad1.temperature(3)
            pt1=ad0.pressure(2)
            vi=svi.value
            vo=svo.value
            writer.writerow([
                t_now-t_start,
                tc1,
                tc2,
                tc3,
                tc4,
                tc5,
                tc6,
                pt1,
                flow_setpoint,
                check,
                flow,
                total,
                bool(vi),
                bool(vo),
            ])
            printout=(
                f'Time:     {t_now-t_start:0.3f} s\n'
                f'Temp 1:   {tc1:0.3f} C\n'
                f'Temp 2:   {tc2:0.3f} C\n'
                f'Temp 3:   {tc3:0.3f} C\n'
                f'Temp 4:   {tc4:0.3f} C\n'
                f'Temp 5:   {tc5:0.3f} C\n'
                f'Temp 6:   {tc6:0.3f} C\n'
                f'Pressure: {pt1:0.3f} barG\n'
                f'Setpoint: {flow_setpoint:0.6f} g/s\n'
                f'Check:    {check:0.6f} g/s\n'
                f'Flow:     {flow:0.6f} g/s\n'
                f'Total:    {total:0.6f} g\n'
                f'Valve In: {bool(vi)}\n'
                f'Valve Out:{bool(vo)}\n'
            )
            print(printout)
            while time.time()-t_now<1:
                pass
        except KeyboardInterrupt:
            try:
                cmd_string=(
                    '\n0 -> Standby\n'
                    '1 -> Fill\n'
                    '2 -> Purge\n'
                    '3 -> New Setpoint\n'
                    '4 -> Reset Mass Total\n'
                    'Any other number to resume\n'
                    'Press ENTER to end script\n'
                )
                cmd=float(input(cmd_string))
                if cmd==0:
                    close()
                    time.sleep(0.2)
                elif cmd==1:
                    close()
                    change_flag=True
                    time.sleep(0.2)
                    svi.on()
                    time.sleep(0.5)
                elif cmd==2:
                    close()
                    time.sleep(0.2)
                    svo.on()
                elif cmd==3:
                    try:
                        setpoint_string=(
                            '\nNew Setpoint Flow\n'
                            f'Maximum {norm2flow:0.6f}\n'
                            'Press ENTER to resume\n'
                            'Entry: '
                        )
                        flow_setpoint=float(input(setpoint_string))
                        change_flag=True
                        print('Setting...')
                    except:
                        print('Resuming...')
                elif cmd==4:
                    total=0
                else:
                    print('Resuming...')
            except:
                print('Ending...')
                close()
                break
        except:
            print('Error...')
            close()
            break
        finally:
            t_prev=t_now

end()

