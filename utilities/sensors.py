import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import time
import gpiozero

def map(x,xmin,xmax,ymin,ymax):
    return (x-xmin)*(ymax-ymin)/(xmax-xmin)+ymin

class EMA:

    def __init__(self,alpha=1,min_alpha=0.5):
        self.alpha=alpha
        self.min_alpha=sorted([0,min_alpha,0.5])[1] # [min_alpha] can be (0 <-> 0.5)
        self.value=None

    def filter(self,now):
        if self.value is None:
            self.value=now
        else:
            self.value=self.alpha * now + (1.0-self.alpha) * self.value
        return self.value

    @property
    def alpha(self):
        return self.alpha

    @alpha.setter
    def alpha(self,new_alpha):
        self.alpha=sorted([self.min_alpha,new_alpha,1.0])[1] # [alpha] can be ([min_alpha] <-> 1.0)

class ADS1115:

    def __init__(self,addr=0x48):
        bus=busio.I2C(board.SCL,board.SDA)
        self.ads=ADS.ADS1115(
            bus,
            address=addr,
            gain=2/3,
            data_rate=64
            )
        self.a0=AnalogIn(self.ads,ADS.P0)
        self.a1=AnalogIn(self.ads,ADS.P1)
        self.a2=AnalogIn(self.ads,ADS.P2)
        self.a3=AnalogIn(self.ads,ADS.P3)

    @property
    def voltage(self):
        return {
            0:self.a0.voltage,
            1:self.a1.voltage,
            2:self.a2.voltage,
            3:self.a3.voltage
        }

    def pressure(self,pin=2,res=165,max_bar=68.95):
        v=self.voltage
        if pin not in [2]:
            print(f'PIN {pin} IS A TC')
            return None
        try:
            volt=v[pin]
        except:
            print('Invalid pin')
            return None
        return map(volt/res,0.004,0.020,0.0,max_bar)

    def temperature(self,pin=0,offset=0):
        v=self.voltage
        if pin not in [0,1,3]:
            print('PIN 2 IS A PT')
        try:
            volt=v[pin]
        except:
            print('Invalid pin')
            return None
        return (volt-offset)/0.005

def rpi_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_str = f.readline()
            temp_c = int(temp_str) / 1000.0  # Convert millidegree to degree
            return temp_c
    except FileNotFoundError:
        return None

class megaTC:

    def __init__(self,spi_bus,s0=5,s1=6,s2=13):
        self.spi=spi_bus # busio object
        while not self.spi.try_lock():
            pass
        self.spi.configure(baudrate=100000,phase=0,polarity=0)
        self.spi.unlock()

        self.S0=gpiozero.OutputDevice(pin=s0)
        self.S1=gpiozero.OutputDevice(pin=s1)
        self.S2=gpiozero.OutputDevice(pin=s2)

    def _read(self,num=0):
        data=bytearray(4)
        self.S0.value=num & 0b001
        self.S1.value=(num & 0b010)>>1
        self.S2.value=(num & 0b100)>>2
        time.sleep(0.01)
        while not self.spi.try_lock():
            pass
        self.spi.readinto(data)
        self.spi.unlock()
        parse={
            'slot':     num,
            'temp':     ((data[0]<<8 | data[1])>>2)/4,
            'fault':    data[1] & 0b1,
            'ref':      ((data[2]<<8 | data[3])>>4)/16,
            'SCV':      data[3] & 0b100,
            'SCG':      data[3] & 0b10,
            'OC':       data[3] & 0b1,
        }
        return parse
    
    def temp(self,pos=0):
        output=self._read(num=pos)
        ret=[output['slot'],output['temp'],output['ref']]
        if output['fault']:
            if output['SCV']: ret.append('f_SCV')
            if output['SCG']: ret.append('f_SCG')
            if output['OC']: ret.append('f_OC')
        return ret


if __name__=='__main__':
    
    ads0=ADS1115(addr=0x48)
    ads1=ADS1115(addr=0x49)
    # ads.ads.data_rate=64
    # Note: TC offset=1.25
    t_start=time.time()
    while True:
        try:
            t_now=time.time()
            # string=(
            #     f'A0:   {ads.voltage[0]:.3f}V   {ads.temperature(0,offset=1.25):.3f}C   {ads.pressure(0):.3f}barg\n'
            #     f'A1:   {ads.voltage[1]:.3f}V   {ads.temperature(1,offset=1.25):.3f}C   {ads.pressure(1):.3f}barg\n'
            #     f'A2:   {ads.voltage[2]:.3f}V   {ads.temperature(2,offset=1.25):.3f}C   {ads.pressure(2):.3f}barg\n'
            #     f'A3:   {ads.voltage[3]:.3f}V   {ads.temperature(3,offset=1.25):.3f}C   {ads.pressure(3):.3f}barg\n'
            # )
            string=(
                f'TIME: {t_now-t_start:.3f} s\n'
                f'T_1 (ads0):  {ads0.temperature(0):.3f} C\n'
                f'T_3 (ads0):  {ads0.temperature(3):.3f} C\n'
                f'T_2 (ads0):  {ads0.temperature(1):.3f} C\n'
                f'P_V (ads0):  {ads0.pressure(2):.3f} barG\n'
                f'T_4 (ads1):  {ads1.temperature(0):.3f} C\n'
                f'T_6 (ads1):  {ads1.temperature(3):.3f} C\n'
                f'T_5 (ads1):  {ads1.temperature(1):.3f} C\n'
                f'P_V (ads1):  {ads1.pressure(2):.3f} barG\n'
            )

            print(string)
            while time.time()-t_now<1:
                pass
        except KeyboardInterrupt:
            break
        
