from transitions import Machine
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
import sqlite3
import atexit

R_p = 165

# Initialize I2C and ADS1115 Sensors
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c, address=0x49)
ads2 = ADS.ADS1115(i2c, address=0x48)
ads3 = ADS.ADS1115(i2c, address=0x4B)

ads.data_rate = 32  # Lower to 32 SPS for more stable readings
ads2.data_rate = 32
ads3.data_rate = 32

c1 = AnalogIn(ads, ADS.P1)
c2 = AnalogIn(ads, ADS.P2)
d2 = AnalogIn(ads2, ADS.P2)
flow_pin = AnalogIn(ads3, ADS.P0)
bottle_pin = AnalogIn(ads3, ADS.P3)

# Configuration Settings
n_cycles = 2
mode = "prod"

if mode == "dev": 
    long_cycle = 10
    p_fill = 5
elif mode == "prod":
    long_cycle = 1800
    p_fill = 30
elif mode == "leak":
    p_fill = 3
    long_cycle = 6000

# SQLite Setup
DB_FILE = "cycling_log_amir.db"

def initialize_database():
    """Creates the SQLite database and table if they don't exist."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS state_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            state TEXT,
            initial_sv_pressure REAL,
            final_sv_pressure REAL,
            ambient_temperature REAL,
            grams REAL,
            cycle INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def calculate_grams(initial_sv_pressure, final_sv_pressure, ambient_temperature):
    """Function to calculate grams in Sieverts apparatus."""
    V_vessel = 5.604 * 3  # Liters
    extra_v = 0.05  # Liters
    V_tot = V_vessel + extra_v
    dp_meas = initial_sv_pressure - final_sv_pressure
    R = 8.3144598  # J / (mol K)
    n = V_tot / 1000 * (dp_meas * 100000) / (R * ambient_temperature)
    grams = n * 2.01588
    return grams

def get_ambient_temperature():
    """Simulated function to return ambient temperature."""
    return 295  # Replace with actual temperature reading

def update_state(state_name, initial_sv_pressure=None, final_sv_pressure=None, ambient_temperature=None, grams=None, cycle=None):
    """Logs state changes in the database."""
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO state_log (timestamp, state, initial_sv_pressure, final_sv_pressure, 
                                   ambient_temperature, grams, cycle)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, state_name, initial_sv_pressure, final_sv_pressure, ambient_temperature, grams, cycle))
        
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Database write failed: {e}")
    finally:
        conn.close()

    print(f"[{timestamp}] State changed: {state_name}, Cycle: {cycle}")

def get_pressure(sensor):
    """Reads pressure values from ADS1115."""
    def map_float(x: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    p_bottle = map_float(bottle_pin.voltage / R_p, 0.004, 0.020, 0.0, 68.95)
    p_control_volume = map_float(c2.voltage / R_p, 0.004, 0.020, 0.0, 68.95)
    p_sample = map_float(d2.voltage / R_p, 0.004, 0.020, 0.0, 68.95)

    pressures = {
        "bottle": p_bottle,
        "control_volume": p_control_volume,
        "sample": p_sample
    }
    return pressures[sensor]

# Define GPIO pins for the solenoids (valves)
valve_sample = LED(16)
valve_bottle = LED(23)
valve_desorb = LED(24)

# State Machine States
states = ["default", "tank_fill", "absorb", "desorb"]

class ValveStateMachine:
    def __init__(self, cycles):
        self.n_cycles = cycles
        self.current_cycle = 0
        self.machine = Machine(model=self, states=states, initial="default")
        
        self.machine.add_transition("start_tank_fill", "default", "tank_fill", after="tank_fill_action")
        self.machine.add_transition("start_absorb", "tank_fill", "absorb", after="absorb_action")
        self.machine.add_transition("start_desorb", "absorb", "desorb", after="desorb_action")
        self.machine.add_transition("reset", ["desorb", "tank_fill"], "default", after="default_action")

    def default_action(self):
        """Set default state: All valves closed."""
        valve_sample.off()
        valve_bottle.off()
        valve_desorb.off()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] State: DEFAULT (All valves closed)")

        if self.current_cycle < self.n_cycles:
            self.current_cycle += 1
            print(f"Starting cycle {self.current_cycle}/{self.n_cycles}...")
            time.sleep(2)
            self.start_tank_fill()
        else:
            print(f"Completed all {self.n_cycles} cycles.")

    def tank_fill_action(self):
        """Tank fill process: Open bottle, wait for pressure to reach setpoint."""
        valve_bottle.on()
        valve_sample.off()
        valve_desorb.off()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] State: TANK FILL (Bottle valve OPEN)")

        while get_pressure("control_volume") < p_fill:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Pressure: {get_pressure('control_volume')} bar")
            time.sleep(1)

        valve_bottle.off()
        time.sleep(2)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Control volume at {get_pressure('control_volume')} bar. Closing bottle.")
        self.start_absorb()

    def absorb_action(self):
        """Absorb process: Open sample valve, hold for set duration."""
        valve_sample.on()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] State: ABSORB (Sample valve OPEN)")

        initial_sv_pressure = get_pressure("control_volume")
        ambient_temperature = get_ambient_temperature()
        
        update_state("ABSORB START", initial_sv_pressure, None, ambient_temperature, None, self.current_cycle)
        time.sleep(long_cycle)
        valve_sample.off()

        final_sv_pressure = get_pressure("control_volume")
        grams_value = calculate_grams(initial_sv_pressure, final_sv_pressure, ambient_temperature)

        update_state("ABSORB END", initial_sv_pressure, final_sv_pressure, ambient_temperature, grams_value, self.current_cycle)
        self.start_desorb()

    def desorb_action(self):
        """Desorb process: Open desorb valve, hold for set duration."""
        valve_desorb.on()
        update_state("DESORB START", cycle=self.current_cycle)
        time.sleep(long_cycle)
        valve_desorb.off()
        update_state("DESORB END", cycle=self.current_cycle)
        self.reset()

def close_valves():
    valve_sample.off()
    valve_bottle.off()
    valve_desorb.off()
    print("All valves closed on exit.")

atexit.register(close_valves)

if __name__ == "__main__":
    fsm = ValveStateMachine(n_cycles)
    fsm.default_action()
    input("Press Enter to start Tank Fill...\n")
    fsm.start_tank_fill()