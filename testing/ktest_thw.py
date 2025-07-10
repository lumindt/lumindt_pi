import time
from datetime import datetime
from threading import Thread
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn
import board
import busio
from openpyxl import Workbook, load_workbook
import os

# === CONFIGURATION ===
V_SUPPLY = 3.3        # Supplied voltage to bridge (V)
R_FIXED = 33      # Fixed resistor (Ohms)
LOG_INTERVAL = 0.001  # Time between samples (seconds)
EXCEL_FILE = "resistance_data.xlsx"

# === GLOBAL STOP FLAG ===
stop_flag = False

def input_listener():
    global stop_flag
    while True:
        user_input = input()
        if user_input.strip().lower() == 'stop':
            stop_flag = True
            break

# === ADC SETUP ===
i2c = busio.I2C(board.SCL, board.SDA)
adc = ADS1115(i2c)
adc.gain = 1
channel = AnalogIn(adc, 0, 1)  # Differential mode between A0 and A1

# === EXCEL SETUP ===
if os.path.exists(EXCEL_FILE):
    wb = load_workbook(EXCEL_FILE)
    existing_sheets = wb.sheetnames
    run_numbers = [
        int(name.replace("Run_", "")) for name in existing_sheets if name.startswith("Run_")
    ]
    next_run = max(run_numbers, default=0) + 1
else:
    wb = Workbook()
    default_sheet = wb.active
    wb.remove(default_sheet)
    next_run = 1

sheet_name = f"Run_{next_run}"
ws = wb.create_sheet(title=sheet_name)
ws.append(["Timestamp", "Voltage (V)", "R_var (Ohms)"])

# === START INPUT LISTENER THREAD ===
listener_thread = Thread(target=input_listener, daemon=True)
listener_thread.start()

# === DATA LOGGING LOOP ===
print(f"\nStarted logging to sheet '{sheet_name}' — type 'stop' and press ENTER to end.\n")

try:
    while not stop_flag:
        v_out = channel.voltage
        try:
            x = (R_FIXED / (R_FIXED + R_FIXED)) - (v_out / V_SUPPLY)
            r_var = (R_FIXED * x) / (1 - x)

        except ZeroDivisionError:
            r_var = float('inf')

        timestamp = datetime.now().isoformat(timespec='seconds')
        print(f"[{timestamp}] Voltage: {v_out:.4f} V | R_var: {r_var:.2f} Ω")

        ws.append([timestamp, round(v_out, 4), round(r_var, 2)])
        time.sleep(LOG_INTERVAL)

finally:
    wb.save(EXCEL_FILE)
    print(f"\nLogging stopped. Data saved to '{EXCEL_FILE}' in sheet '{sheet_name}'.")
