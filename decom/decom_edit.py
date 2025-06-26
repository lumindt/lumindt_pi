import time
import csv
import gpiozero
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from utils.sensors import ADS1115, megaTC
from adafruit_mcp4725 import MCP4725

i2c = busio.I2C(board.SCL,board.SDA)
ad0 = ADS1115(bus=i2c,addr=0x48)
ad1 = ADS1115(bus=i2c,addr=0x49)
ad2 = ADS1115(bus=i2c,addr=0x4B)
dac = MCP4725(bus=i2c,addr=0x60)

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

def close():
    dac.normalized_value=0
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
    close()
    flow_setpoint=0
    total=0
    change_flag=False
    t_start=time.time()
    t_prev=0
    while True:
        try:
            t_now=time.time()-t_start
            volts=ad2.voltage
            flow=volts[0]/5*norm2flow if volts[0]/5>=0.03 else 0
            check=volts[1]/5*norm2flow
            total+=flow*(t_now-t_prev)
            if change_flag:
                dac.normalized_value=sorted([0,flow_setpoint/norm2flow,1])[1]
                change_flag=False
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
            pt1=ad0.pressure(2)
            vi=svi.value
            vo=svo.value
            writer.writerow([
                t_now,
                tc1,
                tc2,
                tc3,
                pt1,
                flow_setpoint,
                check,
                flow,
                total,
                bool(vi),
                bool(vo),
            ])
            printout=(
                f'Time:     {t_now:0.3f} s\n'
                f'Temp 1:   {tc1:0.3f} C\n'
                f'Temp 2:   {tc2:0.3f} C\n'
                f'Temp 3:   {tc3:0.3f} C\n'
                f'Pressure: {pt1:0.3f} barG\n'
                f'Setpoint: {flow_setpoint:0.6f} g/s\n'
                f'Check:    {check:0.6f} g/s\n'
                f'Flow:     {flow:0.6f} g/s\n'
                f'Total:    {total:0.6f} g\n'
                f'Valve In: {bool(vi)}\n'
                f'Valve Out:{bool(vo)}\n'
            )
            print(printout)
            while t_now-t_prev<1:
                pass
        except KeyboardInterrupt:
            try:
                cmd_string=(
                    '\n0 -> Standby\n'
                    '1 -> Fill (Reset Mass)\n'
                    '2 -> Purge\n'
                    '3 -> New Setpoint\n'
                    'Any other number to resume\n'
                    'Press ENTER to end script\n'
                )
                cmd=float(input(cmd_string))
                if cmd==0:
                    close()
                elif cmd==1:
                    close()
                    time.sleep(0.2)
                    change_flag=True
                    total=0
                    svi.on()
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
                else:
                    print('Resuming...')
            except:
                print('Ending...')
                close()
        except:
            print('Error...')
            close()
        finally:
            t_prev=t_now

end()
