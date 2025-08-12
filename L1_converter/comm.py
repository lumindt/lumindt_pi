import time
import board
import busio
from gpiozero import OutputDevice
from adafruit_bus_device.spi_device import SPIDevice

# -----------------------------
# SPI Bus Setup (No Auto CS)
# -----------------------------
spi = busio.SPI(clock=board.SCLK, MISO=board.MISO, MOSI=board.MOSI)
while not spi.try_lock():
    pass
spi.configure(baudrate=100000, phase=0, polarity=0)
spi.unlock()

# Shared SPI device wrapper
spi_dev = SPIDevice(spi, chip_select=None)

# -----------------------------
# Base MCP23S08 Class
# -----------------------------
class MCP23S08:
    def __init__(self, bus, cs_pin, address=0x00, direction="output", pullups=False):
        self.bus=bus
        self.cs = OutputDevice(cs_pin, active_high=False, initial_value=False)
        self.address = address & 0x07
        self.direction = direction
        self.pullups = pullups
        self.init_device()

    def _write(self, reg, val):
        opcode = 0x40 | (self.address << 1) | 0  # Write opcode
        buf = bytearray([opcode, reg, val])
        self.cs.on()
        with self.bus as dev:
            dev.write(buf)
        self.cs.off()

    def _read(self, reg):
        opcode = 0x40 | (self.address << 1) | 1  # Read opcode
        tx = bytearray([opcode, reg])
        rx = bytearray(1)
        self.cs.on()
        with self.bus as dev:
            dev.write(tx)
            dev.readinto(rx)
        self.cs.off()
        return rx[0]

    def init_device(self):
        iodir = 0x00 if self.direction == "output" else 0xFF
        gppu = 0xFF if self.pullups else 0x00
        self._write(0x00, iodir)  # IODIR
        self._write(0x06, gppu)   # GPPU
        if self.direction == "output":
            self._write(0x09, 0x81)  # GPIO default LOW
        print(f"Initialized MCP23S08 on GPIO{self.cs.pin.number} (addr={self.address}, dir={self.direction})")

    def write_gpio(self, value):
        if self.direction != "output":
            raise RuntimeError("MCP GPIO not configured for output")
        self._write(0x09, value)

    def read_gpio(self):
        if self.direction != "input":
            raise RuntimeError("MCP GPIO not configured for input")
        return self._read(0x09)

# -----------------------------
# Extended Class with ADS7953
# -----------------------------
class MCPWithADS(MCP23S08):
    def __init__(self, bus, cs_pin, address=0x00):
        super().__init__(bus, cs_pin, address, direction='output', pullups=False)
        self.config=1

    def read_ads_channel(self, channel):
        command = (0x1 << 12) | ((self.config & 0x01) << 11) | ((channel & 0x0F) << 7)
        self.config=0
        tx = bytearray([command >> 8, command & 0xFF])
        rx = bytearray(2)
        ry = bytearray(2)
        rz = bytearray(2)
        self.write_gpio(0b00000001)
        time.sleep(0.001)
        with self.bus as dev:
            dev.write_readinto(tx,rx)
        self.write_gpio(0b10000001)
        self.write_gpio(0b00000001)
        time.sleep(0.001)
        with self.bus as dev:
            dev.write_readinto(tx,rx)
        self.write_gpio(0b10000001)
        self.write_gpio(0b00000001)
        time.sleep(0.001)
        with self.bus as dev:
            dev.write_readinto(tx,rx)
        self.write_gpio(0b10000001)
        result = (rx[0] & 0X0F)<<8 | rx[1]
        channel = rx[0] >> 4
        return [channel,result]

    def repeat(self):
        tx = bytearray([0x00,0x00])
        rx = bytearray(2)
        self.write_gpio(0b00000001)
        time.sleep(0.0001)
        # time.sleep(3)
        with self.bus as dev:
            dev.write_readinto(tx,rx)
            # time.sleep(0.0001)
        self.write_gpio(0b10000001)
        # result = ((rx[0] & 0x0F) << 8) | rx[1]
        result = (rx[0] & 0X0F)<<8 | rx[1]
        channel = rx[0] >> 4
        return [channel,result]
        

# -----------------------------
# Device Setup
# -----------------------------
mcp0 = MCPWithADS(bus=spi_dev, cs_pin=24, address=0x00)
# mcp1 = MCP23S08(bus=spi_dev, cs_pin=25, address=0x02, direction='input', pullups=False)


# raise Exception('Fix ADS tx code')



while True:
    try:
        for i in range(6,8):
            out=mcp0.read_ads_channel(i)
            print(f'Value {i:>2}:{(out[0]):>2}:{out[1]*(2.5/4095*3):>6.3}')
            time.sleep(0.2)
    except KeyboardInterrupt:
        print('\nEnd')
        break
        







