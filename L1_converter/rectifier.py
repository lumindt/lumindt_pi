import gpiozero

class MCP_BASE:

    def __init__(self,bus,cs,address):
        self.spi=bus
        self.cs=gpiozero.OutputDevice(
            pin=cs,
            active_high=False,
            initial_value=False
        )
        self.address=address

    def write(self,reg,cmd):
        tx=bytearray([0x40|self.address<<1|0,reg,cmd])
        self.cs.on()
        while not self.spi.try_lock():
            pass
        self.spi.write(tx)
        self.spi.unlock()
        self.cs.off()

    def read(self,reg):
        tx=bytearray([0x40|self.address<<1|1,reg])
        rx=bytearray(1)
        self.cs.on()
        while not self.spi.try_lock():
            pass
        self.spi.write_readinto(tx,rx)
        self.spi.unlock()
        self.cs.off()
        return rx

class MCP0(MCP_BASE):

    # y=mx+b
    # MOD[n][0] => m : MOD[n][1] => b
    MOD={
        0:  [100,   -50],
        1:  [10/3,  0],
        2:  [100,   -50],
        3:  [10/3,  0],
        4:  [100,   -50],
        5:  [10/3,  0],
        6:  [100,   -50],
        7:  [10/3,  0],
        8:  [201,   0],
        9:  [3,     0],
        10: [2,     0],
        11: [2,     0],
        12: [7.6,   0],
        13: [40,    -60],
        14: [100,   -50],
        15: [1,     0],
    }

    def __init__(self,bus,cs):
        super().__init__(bus,cs,0)
        self.write(0x00,0x00) # Set IODIR to Outputs
        self.write(0x09,0x81) # Set GPIO to Defaults [ 1000 0001 ]
        self.ads_write(cmd=0x3000) # Set Auto 2 Mode
    
    def ads_write(self,cmd):
        tx=bytearray([cmd>>8,cmd & 0x00FF])
        rx=bytearray(2)
        self.write(0x09,0x01)
        while not self.spi.try_lock():
            pass
        self.spi.write_readinto(tx,rx)
        self.spi.unlock()
        self.write(0x09,0x81)
        return rx

    def ads_read(self,channel):
        chl=int(sorted([0,channel,15])[1])
        addr=None
        i=0
        while addr!=chl and i<20:
            resp=self.ads_write(0x0000)
            addr=resp[0] >> 4
            volt=((resp[0] & 0x0F)<<8 | resp[1])/4095*2.5
            i+=1
        val=self.MOD[addr][0]*volt+self.MOD[addr][1]
        return [addr,volt]

class MCP1(MCP_BASE):

    def __init__(self,bus,cs):
        super().__init__(bus,cs,2)

if __name__ == '__main__':

    import time
    import board
    import busio
    from adafruit_bus_device.spi_device import SPIDevice

    spi = busio.SPI(clock=board.SCLK, MISO=board.MISO, MOSI=board.MOSI)
    while not spi.try_lock():
        pass
    spi.configure(baudrate=100000, phase=0, polarity=0)
    spi.unlock()

    mcp0=MCP0(bus=spi,cs=24)
    mcp1=MCP1(bus=spi,cs=25)

    while True:
        try:
            pstr=''
            pstr+='----------------------------------\n'
            for i in range(16):
                resp=mcp0.ads_read(i)
                pstr+=f'Channel: {resp[0]}\t|\tReading: {resp[1]:.2f}\n'
                time.sleep(0.001)
            print(pstr)
            time.sleep(0.5)
        except KeyboardInterrupt:
            break