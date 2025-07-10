<<<<<<< HEAD
import smbus
bus = smbus.SMBus(1)  # Change to 0 if needed
for addr in range(0x03, 0x78):
    try:
        bus.write_quick(addr)
        print("Found device at: 0x%02X" % addr)
    except OSError:
        pass
=======
#!/usr/bin/env python3

import smbus2
import time

# Use I2C bus 1 (typical on Raspberry Pi)
bus = smbus2.SMBus(1)

print("Scanning I2C bus for devices...")

# I2C addresses range from 0x03 to 0x77
found_devices = []

for address in range(0x03, 0x78):
    try:
        bus.write_quick(address)
        found_devices.append(hex(address))
    except OSError:
        pass  # No device at this address

if found_devices:
    print("Found I2C devices at addresses:")
    for device in found_devices:
        print(f"  {device}")
else:
    print("No I2C devices found.")

bus.close()
>>>>>>> bce00e0 (hedgehog scripts)
