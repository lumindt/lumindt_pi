import sqlite3
import time
import random
from datetime import datetime
import sys
import termios
import tty
from gpiozero import LED
from time import sleep
import threading
import board as board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn


R_p=165
#-------------

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c,address=0x49)
ads2 = ADS.ADS1115(i2c, address=0x48)
ads3 = ADS.ADS1115(i2c,address=0x4b)

c1 = AnalogIn(ads, ADS.P1)
c2 = AnalogIn(ads, ADS.P2)
d2 = AnalogIn(ads2, ADS.P2)
tc1 = AnalogIn(ads2, ADS.P0)
cx = AnalogIn(ads3, ADS.P0)
bottle_pin = AnalogIn(ads3, ADS.P3)


DB_FILE = "cycling_log_amir.db"


def initialize_db():
    """Ensures the sensor_data table exists."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Table for real-time sensor data (logged frequently by data_logger.py)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            pressure_bottle REAL,
            pressure_control_volume REAL,
            pressure_sample REAL,
            temp_1 REAL,
            temp_2 REAL,
            temp_3 REAL,
            flow_rate REAL
        )
    ''')

    # Table for state transitions & cycle events (logged by cycling_state_machine.py)
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

    # Enable WAL mode for better concurrency (both scripts writing simultaneously)
    cursor.execute("PRAGMA journal_mode=WAL;")
    conn.commit()
    conn.close()

# Call this once before logging starts
initialize_db()





def log_data():
    """Logs sensor data independently every `n` seconds."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    def map_float(x: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
	    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    
    p_bottle = map_float(bottle_pin.voltage/R_p,0.004,0.020,0.0,68.95)
    p_control_volume = map_float(c2.voltage/R_p,0.004,0.020,0.0,68.95)
    p_sample = map_float(d2.voltage/R_p,0.004,0.020,0.0,68.95)
    flow = (cx.voltage / 5) * 10 #SL/min
    t1 = tc1.voltage/0.005

    sensor_data = {
        "pressure_bottle": p_bottle,
        "pressure_control_volume": p_control_volume,
        "pressure_sample": p_sample,
        "temp_1": t1,
        "temp_2": random.uniform(20, 100),
        "temp_3": random.uniform(20, 100),
        "flow_rate": flow,
    }

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO sensor_data (timestamp, pressure_bottle, pressure_control_volume, pressure_sample,
                                 temp_1, temp_2, temp_3, flow_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, sensor_data["pressure_bottle"], sensor_data["pressure_control_volume"],
          sensor_data["pressure_sample"], sensor_data["temp_1"], sensor_data["temp_2"],
          sensor_data["temp_3"], sensor_data["flow_rate"]))

    conn.commit()
    conn.close()
    print(f"[{timestamp}] Data logged.")

if __name__ == "__main__":
    LOG_INTERVAL = 0.5  # Log every 5 seconds
    while True:
        log_data()
        time.sleep(LOG_INTERVAL)
