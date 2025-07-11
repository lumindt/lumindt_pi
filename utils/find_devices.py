import smbus
bus = smbus.SMBus(1)  # Change to 0 if needed
for addr in range(0x03, 0x78):
    try:
        bus.write_quick(addr)
        print("Found device at: 0x%02X" % addr)
    except OSError:
        pass
