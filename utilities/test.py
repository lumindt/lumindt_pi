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

        # self._assign_ktype(1,rchannel=18)
        self._assign_ktype_double(2,rchannel=18)
        # self._assign_ktype(3,rchannel=18)
        self._assign_ktype_double(4,rchannel=18)
        # self._assign_diode(5,ideality=1.03)
        # self._assign_ktype(6)
        # self._assign_adc(7)
        # self._assign_adc(8)
        # self._assign_ktype(9,rchannel=18)
        # self._assign_ktype(10,rchannel=18)
        # self._assign_adc(11)
        # self._assign_adc(12)
        # self._assign_adc(13)
        # self._assign_adc(14)
        # self._assign_adc(15)
        self._assign_sense(16)
        # self._assign_adc(17)
        self._assign_rtd(18,rchannel=16)
        # self._assign_adc(19)
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

    def _assign_sense(self,channel):
        addr=0x200+4*(channel-1)
        TYPE=0b11101<<27
        OHMS=502*(2**10)
        cmd=list((TYPE|OHMS).to_bytes(4))
        self._write(addr,cmd)

    def volt(self,channel):
        self._write(0x000,list((0b100<<5|channel).to_bytes(1)))
        time.sleep(0.6)
        addr=0x010+4*(channel-1)
        out = self._read(addr,4)
        flt = [(out[0] & 2**i) >>i for i in reversed(range(8))]
        num = int.from_bytes(out[1:], 'big', signed=True)/(2**21)
        return channel,flt,num

    def temp(self,channel=1):
        # if channel not in range(1,11):
        #     raise ValueError("Channel must be between 1 and 10")
        self._write(0x000,list((0b100<<5|channel).to_bytes(1)))
        time.sleep(0.3)
        addr=0x010+4*(channel-1)
        out = self._read(addr,4)
        flt = [(out[0] & 2**i) >>i for i in reversed(range(8))]
        num = int.from_bytes(out[1:], 'big', signed=True)/1024
        return channel,flt,num
    
    def close(self):
        self.cs.off()
        self.cs.close()

if __name__ == "__main__":
    spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
    LTC=LTC2983(spi, cs=5)
    time.sleep(1)
    # print(LTC._read(0x238,1)[0])
    # for i in range(1,21):
    #     print(LTC.volt(i))
    # print(LTC.temp(1))
    # print(LTC.temp(5))
    file='outputs/salt.csv'
    with open(file, 'w', newline='') as f:
        writer=csv.writer(f)
        writer.writerow([
            'Time (s)',
            'RTD',
            # 'TC1',
            'TC2',
            # 'TC3',
            'TC4',
        ])
        t_start=time.time()
        while True:
            t_now=time.time()
            RTD=LTC.temp(18)[2]
            # TC1=LTC.temp(1)[2]
            TC2=LTC.temp(2)[2]
            # TC3=LTC.temp(3)[2]
            TC4=LTC.temp(4)[2]

            writer.writerow([
                t_now-t_start,
                RTD,
                # TC1,
                TC2,
                # TC3,
                TC4
            ])

            string=(
                f'{"":-^30}\n'
                f'Time:     {t_now-t_start:0.3f} s\n'
                f'RTD:      {RTD:0.3f} C\n'
                # f'TC1:      {TC1:0.3f} C\n'
                f'TC2:      {TC2:0.3f} C\n'
                # f'TC3:      {TC3:0.3f} C\n'
                f'TC4:      {TC4:0.3f} C\n'
            )
            print(string)
            while time.time()-t_now<2:
                pass
                
    LTC.close()

