from utils.sensors import megaTC
import board
import busio
import time

spi=busio.SPI(clock=board.SCLK,MISO=board.MISO)
while not spi.try_lock():
    pass
spi.configure(baudrate=100000,phase=0,polarity=0)
spi.unlock()

TC=megaTC(spi_bus=spi)
i=0
while True:
    ret=TC.temp(i)
    # print(f'Slot:\t{ret[0]:>2}\t|\tTemp:\t{ret[1]:>6}\t|\tRef:\t{ret[2]:>8}')
    print(ret)
    time.sleep(0.5)
    if i==7:
        i=0
    else:
        i+=1