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
flow_pin1 = AnalogIn(ads3, ADS.P0)
flow_pin2 = AnalogIn(ads3, ADS.P1)
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

# Function to read flow sensor values
def get_flow_rate(sensor):
    if sensor == "flow1":
        return flow_pin1.voltage
    elif sensor == "flow2":
        return flow_pin2.voltage
    return None

# Function to log flow rates
def log_flow_rates():
    flow1 = get_flow_rate("flow1")
    flow2 = get_flow_rate("flow2")
    print(f"Flow Sensor 1: {flow1} V, Flow Sensor 2: {flow2} V")
    return flow1, flow2

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
            cycle INTEGER,
            flow1 REAL,
            flow2 REAL
        )
    ''')
    conn.commit()
    conn.close()

def update_state(state_name, initial_sv_pressure=None, final_sv_pressure=None, ambient_temperature=None, grams=None, cycle=None):
    """Logs state changes in the database."""
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        flow1, flow2 = log_flow_rates()
        cursor.execute('''
            INSERT INTO state_log (timestamp, state, initial_sv_pressure, final_sv_pressure, 
                                   ambient_temperature, grams, cycle, flow1, flow2)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, state_name, initial_sv_pressure, final_sv_pressure, ambient_temperature, grams, cycle, flow1, flow2))
        
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Database write failed: {e}")
    finally:
        conn.close()
    
    print(f"[{timestamp}] State changed: {state_name}, Cycle: {cycle}, Flow1: {flow1}, Flow2: {flow2}")

def close_valves():
    print("All valves closed on exit.")

atexit.register(close_valves)

if __name__ == "__main__":
    initialize_database()
    log_flow_rates()
    print("Flow readings updated with second flow sensor.")
