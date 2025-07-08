import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import time

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
            3:self.a3.voltage,
            
        }
    def pressure(self):
        v=self.voltage

        return v


if __name__=='__main__':
    
    ads=ADS1115(addr=0x48)
    # Note: TC offset=1.25
    while True:
        try:
            t_start=time.time()
            # string=(
            #     f'A0:   {ads.voltage[0]:.3f}V   {ads.temperature(0,offset=1.25):.3f}C   {ads.pressure(0):.3f}barg\n'
            #     f'A1:   {ads.voltage[1]:.3f}V   {ads.temperature(1,offset=1.25):.3f}C   {ads.pressure(1):.3f}barg\n'
            #     f'A2:   {ads.voltage[2]:.3f}V   {ads.temperature(2,offset=1.25):.3f}C   {ads.pressure(2):.3f}barg\n'
            #     f'A3:   {ads.voltage[3]:.3f}V   {ads.temperature(3,offset=1.25):.3f}C   {ads.pressure(3):.3f}barg\n'
            # )
            string=(
                f'V:  {ads.pressure()} \n'
            )
            print(string)
            while time.time()-t_start<1:
                pass
        except KeyboardInterrupt:
            break
        
