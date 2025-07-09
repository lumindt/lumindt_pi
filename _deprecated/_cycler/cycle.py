import time
import board as board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import gpiozero

R_p=165

def map_float(x: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
	return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

i2c = busio.I2C(board.SCL, board.SDA)
ads0 = ADS.ADS1115(i2c)
tc1 = AnalogIn(ads0, ADS.P0)
tc2 = AnalogIn(ads0, ADS.P1)
pt1 = AnalogIn(ads0, ADS.P2)
tc3 = AnalogIn(ads0, ADS.P3)

ads1 = ADS.ADS1115(i2c,address=0x49)
tc4 = AnalogIn(ads1, ADS.P0)
tc5 = AnalogIn(ads1, ADS.P1)
pt2 = AnalogIn(ads1, ADS.P2)
tc6 = AnalogIn(ads1, ADS.P3)

ads2 = ADS.ADS1115(i2c,address=0x4B)
fm1 = AnalogIn(ads2, ADS.P0)
fm2 = AnalogIn(ads2, ADS.P1)

sv1 = gpiozero.OutputDevice(23)
sv2 = gpiozero.OutputDevice(24)

def avg_read_tc(chan,samples=3):
    val=0
    for _ in range(samples):
        val+=chan.voltage/0.005/samples
        time.sleep(0.01)
    return val

def avg_read_pt(chan,samples=5):
    val=0
    for _ in range(samples):
        val+=map_float(chan.voltage/165,0.004,0.016,0.000,68.95)/samples
        time.sleep(0.01)
    return val

def avg_read_fm(chan,samples=8):
    val=0
    for _ in range(samples):
        val+=chan.voltage/(5/10/1.0106)/samples
        time.sleep(0.01)
    return val


class CYCLE_FSM():
    
    def __init__(self):

        self.handler=self._handler_coroutine()
        next(self.handler)
        self.handler.send(0)

    def _handler_coroutine(self,command):
        while True:
            command=yield
            if command==2:
                self._m_abs()
            elif command==3:
                self._m_des()
            elif command==4:
                self._a_abs()
            elif command==5:
                self._wait()
            elif command==6:
                self._a_des()
            elif command==7:
                self._refill()
            else:
                self._standby()

    def _standby(self):
        print('Standby...')
        # NO FLOW

    def _m_abs(self):
        print('Manual Absorb...')
        # FLOW IN

    def _m_des(self):
        print('Manual Desorb...')
        # FLOW OUT

    def _a_abs(self):
        print('Auto Absorb...')
        # FLOW IN

    def _wait(self):
        print('Wait...')
        # NO FLOW

    def _a_des(self):
        print('Auto Desorb...')
        # FLOW OUT
    
    def _refill(self):
        print('Refill Required...')
        # NO FLOW

cycler=CYCLE_FSM()

loop_time=3
t_init=time.time()
while(True):
    try:
        t_start=time.time()
        string=(f'SEC: {t_start-t_init:0.3f}\n'
                # f'TC1: {avg_read_tc(tc1):0.3f}\n'
                # f'TC2: {avg_read_tc(tc2):0.3f}\n'
                # f'TC3: {avg_read_tc(tc3):0.3f}\n'
                # f'TC4: {avg_read_tc(tc4):0.3f}\n'
                # f'TC5: {avg_read_tc(tc5):0.3f}\n'
                # f'TC6: {avg_read_tc(tc6):0.3f}\n'
                f'PT1: {avg_read_pt(pt1):0.3f}\n'
                f'PT2: {avg_read_pt(pt2):0.3f}\n'
                f'FM1: {avg_read_fm(fm1):0.3f}\n'
                f'FM2: {avg_read_fm(fm2):0.3f}\n'
                )
        print(string)



        while time.time()-t_start<loop_time:
            pass
    except KeyboardInterrupt:
        try:
            command=float(input('1: Standby\n2: Manual Absorb\n3: Manual Desorb\n4: Auto\nPress Enter to Exit\n\nEntry: '))
            if command==4:
                # m_abs
                pass
        except:
            break

sv1.off()
sv2.off()
sv1.close()
sv2.close()