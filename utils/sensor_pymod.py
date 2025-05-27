import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import time

def map(x,xmin,xmax,ymin,ymax):
    return (x-xmin)*(ymax-ymin)/(xmax-xmin)+ymin

#class EMA:
       # self.alpha=sorted([self.min_alpha,new_alpha,1.0])[1] # [alpha] can be ([min_alpha] <-> 1.0)

class ADS1115:

    def __init__(self,addr=0x48):
        bus=busio.I2C(board.SCL,board.SDA)

        self.ads=ADS.ADS1115(bus, address=addr)

        # Define allowed options
        self.rates = [8, 16, 32, 64, 128, 250, 475, 860]
        self.gains = [2/3, 1, 2, 4, 8, 16]

        # Initialize private properties with defaults
        self._gain = 2/3
        self._data_rate = 64
        self.initialized = True

        self._write_config()

        self.a0=AnalogIn(self.ads,ADS.P0)
        self.a1=AnalogIn(self.ads,ADS.P1)
        self.a2=AnalogIn(self.ads,ADS.P2)
        self.a3=AnalogIn(self.ads,ADS.P3)

    def _write_config(self):
        self.ads.gain = self._gain
        self.ads.data_rate = self._data_rate

    @property
    def data_rate(self) -> int:        
        return self._data_rate

    @data_rate.setter
    def data_rate(self, rate: int) -> None:
        if rate not in self.rates:
            raise ValueError(f"Data rate must be one of: {self.rates}")
        self._data_rate = rate
        if self.initialized:
            self._write_config()

    @property
    def gain(self) -> float:
        return self._gain

    @gain.setter
    def gain(self, gain: float) -> None:
        if gain not in self.gains:
            raise ValueError(f"Gain must be one of: {self.gains}")
        self._gain = gain
        if self.initialized:
            self._write_config()

    @property
    def voltage(self):
        return {
            0:self.a0.voltage,
            1:self.a1.voltage,
            2:self.a2.voltage,
            3:self.a3.voltage
        }

    def pressure(self,pin=0,res=165,max_bar=68.95):
        v=self.voltage
        try:
            volt=v[pin]
        except:
            print('Invalid pin')
            return None
        return map(volt/res,0.004,0.020,0.0,max_bar)

    def temperature(self,pin=0,offset=0):
        v=self.voltage
        try:
            volt=v[pin]
        except:
            print('Invalid pin')
            return None
        return (volt-offset)/0.005

if __name__=='__main__':
    
    # Note: TC offset=1.25
    sensor_map = {
        'TC1': (0x48, 0, 'temp'),
        'TC2': (0x48, 1, 'temp'),
        'TC3': (0x48, 3, 'temp'),
        'PT1': (0x48, 2, 'press'),
        'TC4': (0x49, 0, 'temp'),
        'TC5': (0x49, 1, 'temp'),
        'TC6': (0x49, 3, 'temp'),
        'PT2': (0x49, 2, 'press')
    }
    # Initialize both ADS1115 devices
    ads_48 = ADS1115(addr=0x48)
    ads_49 = ADS1115(addr=0x49)

    try:
        while True:
            #t_start = time.time()
            user_input = input("Enter sensor name or 'q' to quit: ").strip().upper()
            if user_input == 'Q':
                print("Exiting.")
                break
            if user_input not in sensor_map:
                print("Invalid sensor name.")
                continue

            addr, pin, kind = sensor_map[user_input]
            ads = ads_48 if addr == 0x48 else ads_49

            if kind == 'temp':
                value = ads.temperature(pin, offset=0)
                print(f"{user_input}: {value:.2f} °C")
            elif kind == 'press':
                value = ads.pressure(pin)
                print( f"{user_input}: {value:.2f} barG")
                
            # Delay until 1 second has passed
            #while time.time() - t_start < 1:
                #pass
            ads.gain=2/3
            ads.data_rate=64
    except KeyboardInterrupt:
        print("\nExiting program.")
            