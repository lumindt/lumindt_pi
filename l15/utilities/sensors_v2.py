import board
import busio
import gpiozero
import time
import csv

class LTC2983:

    R_CMD = 0x03
    W_CMD = 0x02

    def __init__(self, spi, cs=5):
        self.spi = spi
        while not self.spi.try_lock():
            pass
        self.cs = gpiozero.OutputDevice(pin=cs,active_high=False)
        self.spi.configure(baudrate=1000000, polarity=0, phase=0)
        self.spi.unlock()

        self._assign_ktype(1)
        self._assign_ktype(2)
        self._assign_ktype(3)
        self._assign_ktype(4)
        self._assign_ktype(5)
        self._assign_ktype(6)
        self._assign_ktype(7)
        self._assign_ktype(8)
        self._assign_ktype(9)
        self._assign_ktype(10)
        self._assign_adc(11)
        self._assign_adc(12)
        self._assign_adc(13)
        self._assign_adc(14)
        # self._assign_adc(15)
        self._assign_sense(16,ohms=502)
        # self._assign_adc(17)
        self._assign_rtd(18,rchannel=16)
        self._assign_adc(19)
        self._assign_diode(20,ideality=1.85)




    def _write(self,reg,cmd):
        tx=bytearray([self.W_CMD,(reg>>8)&0xff,reg&0xff,*cmd])
        self.cs.on()
        while not self.spi.try_lock():
            pass
        self.spi.write(tx)
        # time.sleep(0.1)
        self.spi.unlock()
        self.cs.off()

    def _read(self,reg,ret):
        tx=bytearray([self.R_CMD,(reg>>8)&0xff,reg&0xff])
        rx=bytearray(ret)
        self.cs.on()
        while not self.spi.try_lock():
            pass
        self.spi.write(tx)
        # time.sleep(0.1)
        self.spi.readinto(rx)
        # time.sleep(0.1)
        self.spi.unlock()
        self.cs.off()
        return rx

    def _assign_ktype(self,channel,rchannel=18):
        addr=0x200+4*(channel-1)
        TYPE=0b00010<<27
        CJCH=rchannel<<22
        SENS=0b1000<<18
        cmd=list((TYPE|CJCH|SENS).to_bytes(4))
        self._write(addr,cmd)

    def _assign_ktype_double(self,channel,rchannel=18):
        addr=0x200+4*(channel-1)
        TYPE=0b00010<<27
        CJCH=rchannel<<22
        SENS=0b0000<<18
        cmd=list((TYPE|CJCH|SENS).to_bytes(4))
        self._write(addr,cmd)

    def _assign_diode(self,channel,ideality=1):
        addr=0x200+4*(channel-1)
        TYPE=0b11100<<27
        SENS=0b111<<24
        CURR=0b00<<22
        FCTR=int(ideality*2**20)
        cmd=list((TYPE|SENS|CURR|FCTR).to_bytes(4))
        self._write(addr,cmd)

    def _assign_adc(self,channel):
        addr=0x200+4*(channel-1)
        TYPE=0b11110<<27
        ENDS=0b1<<26
        cmd=list((TYPE|ENDS).to_bytes(4))
        self._write(addr,cmd)

    def _assign_rtd(self,channel,rchannel=16):
        addr=0x200+4*(channel-1)
        TYPE=0b01111<<27
        REFR=rchannel<<22
        CONF=0b0001<<18
        XCUR=0b1000<<14
        CURV=0b01<<12
        cmd=list((TYPE|REFR|CONF|XCUR|CURV).to_bytes(4))
        self._write(addr,cmd)

    def _assign_sense(self,channel,ohms=500):
        addr=0x200+4*(channel-1)
        TYPE=0b11101<<27
        OHMS=ohms*(2**10)
        cmd=list((TYPE|OHMS).to_bytes(4))
        self._write(addr,cmd)

    def volt(self,channel):
        if channel not in range(15,20):
            raise ValueError("Channel must be between 15 and 19")
        self._write(0x000,list((0b100<<5|channel).to_bytes(1)))
        time.sleep(0.6)
        addr=0x010+4*(channel-1)
        out = self._read(addr,4)
        flt = [(out[0] & 2**i) >>i for i in reversed(range(8))]
        num = int.from_bytes(out[1:], 'big', signed=True)/(2**21)
        return num

    def temp(self,channel=1):
        # if channel not in range(1,11):
        #     raise ValueError("Channel must be between 1 and 10")
        self._write(0x000,list((0b100<<5|channel).to_bytes(1)))
        time.sleep(0.3)
        addr=0x010+4*(channel-1)
        out = self._read(addr,4)
        flt = [(out[0] & 2**i) >>i for i in reversed(range(8))]
        num = int.from_bytes(out[1:], 'big', signed=True)/1024
        return num

    def pres(self,channel=11):
        if channel not in range(11,15):
            raise ValueError("Channel must be between 11 and 14")
        self._write(0x000,list((0b100<<5|channel).to_bytes(1)))
        time.sleep(0.6)
        addr=0x010+4*(channel-1)
        out = self._read(addr,4)
        flt = [(out[0] & 2**i) >>i for i in reversed(range(8))]
        num = int.from_bytes(out[1:], 'big', signed=True)/(2**21)
        pt_reading=(num/165-0.004)*(68.95/0.016)
        return pt_reading
    
    def close(self):
        self.cs.off()
        self.cs.close()

if __name__ == "__main__":
    spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
    LTC=LTC2983(spi)
    time.sleep(1)
    t_start=time.time()
    while True:
        try:
            t_now=time.time()
            PT1=LTC.pres(11)
            PT2=LTC.pres(12)
            PT3=LTC.pres(13)
            PT4=LTC.pres(14)
            REF=LTC.temp(18)
            TC1=LTC.temp(1)
            TC2=LTC.temp(2)
            TC3=LTC.temp(3)
            TC4=LTC.temp(4)

            string=(
                f'{"":-^30}\n'
                f'Time:     {t_now-t_start:0.3f}\n'
                f'PT1:      {PT1:0.3f} barG\n'
                f'PT2:      {PT2:0.3f} barG\n'
                f'PT3:      {PT3:0.3f} barG\n'
                f'PT4:      {PT4:0.3f} barG\n'
                f'REF:      {REF:0.3f} °C\n'
                # f'TC1:      {TC1:0.3f} °C\n'
                # f'TC2:      {TC2:0.3f} °C\n'
                # f'TC3:      {TC3:0.3f} °C\n'
                # f'TC4:      {TC4:0.3f} °C\n'
                f'TC1:      {2*REF-TC1:0.3f} °C\n'
                f'TC2:      {2*REF-TC2:0.3f} °C\n'
                f'TC3:      {2*REF-TC3:0.3f} °C\n'
                f'TC4:      {2*REF-TC4:0.3f} °C\n'
            )
            print(string)
            while time.time()-t_now<2:
                pass
        except KeyboardInterrupt:
            break
    LTC.close()

