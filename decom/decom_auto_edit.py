import time
import csv
import gpiozero
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from utils.sensors import ADS1115, megaTC
from adafruit_mcp4728 import MCP4728

i2c = busio.I2C(board.SCL,board.SDA)
ad0 = ADS1115(bus=i2c,addr=0x48)
ad1 = ADS1115(bus=i2c,addr=0x49)
ad2 = ADS1115(bus=i2c,addr=0x4B)
dac = MCP4728(i2c,address=0x60)

spi=busio.SPI(clock=board.SCLK,MISO=board.MISO)
while not spi.try_lock():
    pass
spi.configure(baudrate=100000,phase=0,polarity=0)
spi.unlock()
mtc = megaTC(spi_bus=spi,s0=5,s1=6,s2=13)

svi=gpiozero.OutputDevice(pin=17)
svo=gpiozero.OutputDevice(pin=27)

# Conversion of normalized value to flow in g/s
norm2flow=10*0.9926*1.427/60

setpoint=0
total=0
mode=0
def operation(op=0):
    if op==1:
        # Fill
        svo.off()
        time.sleep(0.1)
        svi.on()
        time.sleep(0.1)
        dac.channel_a.normalized_value=sorted([0,setpoint/norm2flow,1])[1]
        return 1
    elif op==2:
        # Purge
        svi.off()
        time.sleep(0.1)
        svo.on()
        time.sleep(0.1)
        dac.channel_a.normalized_value=0
        return 2
    elif op==3:
        # Force Purge
        svi.off()
        time.sleep(0.1)
        svo.on()
        time.sleep(0.1)
        dac.channel_a.normalized_value=0
        return 3
    else:
        # Standby
        svi.off()
        svo.off()
        time.sleep(0.1)
        dac.channel_a.normalized_value=0
        return 0

mode=operation(0)

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
        'Vessel Temp 7 (C)',
        'Vessel Temp 8 (C)',
        'Vessel Temp 9 (C)',
        'Vessel Temp 10 (C)',
        'Vessel Temp 11 (C)',
        'Vessel Temp 12 (C)',
        'Vessel Temp 13 (C)',
        'Vessel Temp 14 (C)',
        'Vessel Pressure (barG)',
        'Commanded Flow (g/s)',
        'Command Check (g/s)',
        'Omega Flow Rate (g/s)',
        'Total Mass (g)',
        'Valve In',
        'Valve Out',
    ])
    t_start=time.time()
    t_prev=t_start
    while True:
        try:
            t_now=time.time()
            volts=ad2.voltage
            flow=volts[0]/5*norm2flow #if volts[0]/5>=0.005 else 0
            check=volts[1]/5*norm2flow
            total+=flow*(t_now-t_prev)
            tc1=ad0.temperature(0)
            tc2=ad0.temperature(1)
            tc3=ad0.temperature(3)
            tc4=ad1.temperature(0)
            tc5=ad1.temperature(1)
            tc6=ad1.temperature(3)
            tc7=mtc.temp(0)[1]
            tc8=mtc.temp(1)[1]
            tc9=mtc.temp(2)[1]
            tc10=mtc.temp(3)[1]
            tc11=mtc.temp(4)[1]
            tc12=mtc.temp(5)[1]
            tc13=mtc.temp(6)[1]
            tc14=mtc.temp(7)[1]
            tmx=max([tc1,tc2,tc3,tc4,tc5,tc6,tc7,tc8,tc9,tc10,tc11,tc12,tc13,tc14])
            pt1=ad0.pressure(2)

            if mode==1 and (tmx>45 or pt1>1.5):
                mode=operation(2)
                # time.sleep(30)
            elif mode==2 and tmx<30 and pt1<0.05:
                mode=operation(1)
            else:
                pass

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
                tc7,
                tc8,
                tc9,
                tc10,
                tc11,
                tc12,
                tc13,
                tc14,
                pt1,
                setpoint,
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
                f'Temp 7:   {tc7:0.3f} C\n'
                f'Temp 8:   {tc8:0.3f} C\n'
                f'Temp 9:   {tc9:0.3f} C\n'
                f'Temp 10:  {tc10:0.3f} C\n'
                f'Temp 11:  {tc11:0.3f} C\n'
                f'Temp 12:  {tc12:0.3f} C\n'
                f'Temp 13:  {tc13:0.3f} C\n'
                f'Temp 14:  {tc14:0.3f} C\n'
                f'Pressure: {pt1:0.3f} barG\n'
                f'Setpoint: {setpoint:0.6f} g/s\n'
                f'Check:    {check:0.6f} g/s\n'
                f'Flow:     {flow:0.6f} g/s\n'
                f'Total:    {total:0.6f} g\n'
                f'Valve In: {bool(vi)}\n'
                f'Valve Out:{bool(vo)}\n'
                f'Mode:     {mode}\n'
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
                    '3 -> Force Purge\n'
                    '4 -> New Setpoint\n'
                    '5 -> Reset Mass Total\n'
                    'Any other number to resume\n'
                    'Press ENTER to end script\n'
                )
                cmd=float(input(cmd_string))
                if cmd==0:
                    mode=operation(0)
                elif cmd==1:
                    mode=operation(1)
                elif cmd==2:
                    mode=operation(2)
                elif cmd==3:
                    mode=operation(3)
                elif cmd==4:
                    try:
                        setpoint_string=(
                            '\nNew Setpoint Flow\n'
                            f'Maximum {norm2flow:0.6f}\n'
                            'Press ENTER to resume\n'
                            'Entry: '
                        )
                        setpoint=float(input(setpoint_string))
                        print('Setting...')
                    except:
                        print('Resuming...')
                elif cmd==5:
                    total=0
                else:
                    print('Resuming...')
            except:
                print('Ending...')
                mode=operation(0)
                break
        except:
            print('Error...')
            mode=operation(0)
            break
        finally:
            t_prev=t_now

mode=operation(0)
print(f'\nIN VALVE:\t{bool(svi.value)}\nOUT VALUE:\t{bool(svo.value)}')

