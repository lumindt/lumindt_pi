import sys
import termios
import tty
from gpiozero import LED
import time
from time import sleep
import threading
import board as board
import busio
import adafruit_ads1x15.ads1115 as ADS
from datetime import datetime
from adafruit_ads1x15.analog_in import AnalogIn

# Define GPIO pins for the solenoids
solenoid_absorb = LED(23)
solenoid_desorb = LED(24)


R_p=165
#-------------

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c,address=0x49)
ads2 = ADS.ADS1115(i2c,address=0x48)
ads3 = ADS.ADS1115(i2c,address=0x4b)

ads.data_rate = 32  # Lower to 32 SPS for more stable readings
ads2.data_rate = 32
ads3.data_rate = 32

c1 = AnalogIn(ads, ADS.P1)
c2 = AnalogIn(ads, ADS.P2)
d2 = AnalogIn(ads2, ADS.P2)

flow_pin = AnalogIn(ads3, ADS.P0)






# Map keys to solenoids
solenoids = {
    '1': ('bottle', solenoid_absorb),
    '2': ('sample', solenoid_desorb),

}


# Track solenoid states
solenoid_states = {
    '1': False,
    '2': False,

}

def get_key():
    """Reads a single key press without requiring Enter."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return key

def toggle_solenoid(key):
    """Toggles the solenoid associated with the key."""
    if key in solenoids:
        name, solenoid = solenoids[key]
        solenoid_states[key] = not solenoid_states[key]  # Toggle state
        if solenoid_states[key]:
            print(f"\n{name.capitalize()} ON")
            solenoid.on()
        else:
            print(f"\n{name.capitalize()} OFF")
            solenoid.off()

def map_float(x: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
	return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def print_pressure():
    global pressure
    while True:
        pressure = map_float(c2.voltage/R_p,0.004,0.020,0.0,68.95)
        sample_pressure = map_float(d2.voltage/R_p,0.004,0.020,0.0,68.95)
        timestamp = datetime.now().strftime("%H:%M:%S")  # Get current time
        flow = (flow_pin.voltage / 5) * 10 #SL/min
        sys.stdout.write(f"\r[{timestamp}] Pressure: {pressure:.2f} Bar x Sample Pressure: {sample_pressure:.2f} Bar x Flow: {flow:.2f} SLM")  # Overwrites line        sys.stdout.flush()
        #sys.stdout.write(f"\r[{timestamp}] Sample Pressure: {sample_pressure:.2f} PSI")  # Overwrites line        sys.stdout.flush()

        time.sleep(2)

# def get_flow()
#     global grams
#     while True:
#         flow = (cx.voltage / 5) * 10 #SL/min




def main():
    print("\nPress '1' or '2' to toggle solenoids.")
    print("Press 'q' to quit.\n")

    # Start pressure printing in a separate thread
    pressure_thread = threading.Thread(target=print_pressure, daemon=True)
    pressure_thread.start()

    try:
        while True:
            
            
            key = get_key()
            if key == 'q':
                print("\nExiting script...")
                break
            elif key in solenoids:
                toggle_solenoid(key)
    except KeyboardInterrupt:
        print("\nKeyboard Interrupt detected. Exiting...")
    finally:
        print("Turning off all solenoids and cleaning up...")
        for solenoid in solenoids.values():
            solenoid.off()

if __name__ == "__main__":
    main()
