#!/usr/bin/env python3
import can
import struct
import sys

# Default CAN ID offset (0x50 → Setpoint = 0x50, Status = 0x51, etc.)
ID_OFFSET = 0x50
SETPOINT_ID = 0x000 + ID_OFFSET

# ⚠️ CT-3001 limits (check your datasheet for exact motor!)
MIN_RPM = 10000     # below this startup may stall
MAX_RPM = 300000    # CT-3001 absolute max

def send_setpoint(start=False, ack=False, speed_rpm=0):
    """Send a setpoint message to the Celeroton CT-3001."""

    bus = can.interface.Bus(channel="can0", bustype="socketcan")

    # First byte = opCmd1 control bits
    opCmd1 = 0
    if start:
        opCmd1 |= 0x01  # Start/Stop
    if ack:
        opCmd1 |= 0x02  # Error acknowledge

    opCmd2 = 0x00
    reserved = [0x00, 0x00]

    # Speed is signed int32, big endian
    speed_bytes = struct.pack(">i", int(speed_rpm))

    data = bytearray([opCmd1, opCmd2] + reserved) + speed_bytes
    msg = can.Message(arbitration_id=SETPOINT_ID,
                      data=data,
                      is_extended_id=False)
    bus.send(msg)

    print(f"✅ Sent Setpoint → start={start}, ack={ack}, speed={speed_rpm} rpm")

def usage():
    print("Available commands: start, stop, ack")
    print("Usage:")
    print("  python3 celeroton_control.py start <rpm>")
    print("  python3 celeroton_control.py stop")
    print("  python3 celeroton_control.py ack")
    print("\nArguments:")
    print(f"  <rpm>   integer between {MIN_RPM} and {MAX_RPM}")
    print("\nExamples:")
    print("  python3 celeroton_control.py start 20000   # start at 20k rpm")
    print("  python3 celeroton_control.py start 70000   # set 70k rpm")
    print("  python3 celeroton_control.py stop          # stop blower")
    print("  python3 celeroton_control.py ack           # acknowledge errors")

def validate_rpm(rpm: int):
    """Ensure RPM is within safe bounds."""
    if rpm < MIN_RPM or rpm > MAX_RPM:
        print(f"❌ Invalid RPM: {rpm}. Must be between {MIN_RPM} and {MAX_RPM}.")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "start":
        if len(sys.argv) != 3:
            print("❌ Please provide an RPM value.")
            usage()
            sys.exit(1)
        try:
            speed = int(sys.argv[2])
        except ValueError:
            print("❌ RPM must be an integer.")
            sys.exit(1)

        validate_rpm(speed)
        send_setpoint(start=True, speed_rpm=speed)

    elif cmd == "stop":
        send_setpoint(start=False, speed_rpm=0)

    elif cmd == "ack":
        send_setpoint(ack=True)

    else:
        usage()
