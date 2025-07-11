import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
from openpyxl import Workbook, load_workbook
import os

# === CONFIGURATION ===
EXCEL_INPUT = "resistance_data.xlsx"
EXCEL_OUTPUT = "ktest_dataprocess.xlsx"
ALPHA = 0.00385            # Temperature coefficient of resistance (1/K)
V_SUPPLY = 3.3             # Voltage applied (V)
L = 0.035                  # Length of wire (m)
q_prime = 0.25              # Heat flux (W/m²)

# === LOAD INPUT EXCEL FILE ===
df = pd.read_excel(EXCEL_INPUT, sheet_name=None)
print("Available runs:", list(df.keys()))

run_name = input("Enter run sheet name (e.g., Run_1): ").strip()
if run_name not in df:
    raise ValueError(f"Sheet '{run_name}' not found in {EXCEL_INPUT}")

data = df[run_name]

# === CONVERT TIMESTAMP TO SECONDS ===
data['Timestamp'] = pd.to_datetime(data['Timestamp'])
data['time_s'] = (data['Timestamp'] - data['Timestamp'].iloc[0]).dt.total_seconds()

# === PLOT R vs TIME ===
plt.plot(data['time_s'], data['R_var (Ohms)'])
plt.xlabel('Time (s)')
plt.ylabel('Resistance (Ω)')
plt.title(f'R vs Time — {run_name}')
plt.grid(True)
print("Saving plot...")
plt.savefig(f"{run_name}_deltaT_vs_ln_time.png")
plt.close()


# === GET R0 FROM USER AND CALCULATE del R ===
R0 = 0
data['del R'] = data['R_var (Ohms)'] - R0

# === COMPUTE del T ===
delR = data['del R'].to_numpy()
r0 = R0
delT = (delR / r0) / ALPHA
data['del T'] = delT


# === PLOT delT vs logtime ===
#log_time = np.log(data['time_s'])
plt.plot(data['time_s'], data['del T'])
plt.xlabel('ln Time (s)')
plt.ylabel('Temperature Rise ΔT (K)')
plt.title(f'ΔT vs Time — {run_name}')
plt.grid(True)
plt.savefig(f"{run_name}_deltaT_vs_time.png")
plt.close()

# === GET TIME RANGE FROM USER ===
tmin = float(input("Enter minimum time (s) for linear fit: "))
tmax = float(input("Enter maximum time (s) for linear fit: "))

fit_data = data[(data['time_s'] >= tmin) & (data['time_s'] <= tmax)]
log_t = np.log(fit_data['time_s'])
delT_fit = fit_data['del T']

# === LINEAR FIT ===
slope, intercept, r_value, p_value, std_err =    linregress(log_t, delT_fit)
print(f"Slope m = {slope:.5f} K")

# === CALCULATE k ===
k = q_prime / (4 * pi*slope)
print(f"Calculated thermal conductivity k = {k:.4f} W/m·K")

# === SAVE TO OUTPUT EXCEL FILE ===
if os.path.exists(EXCEL_OUTPUT):
    wb = load_workbook(EXCEL_OUTPUT)
    ws = wb.active
else:
    wb = Workbook()
    ws = wb.active
    ws.append(["Run", "k (W/m·K)"])

ws.append([run_name, round(k, 5)])
wb.save(EXCEL_OUTPUT)
print(f"Saved k to {EXCEL_OUTPUT} under run '{run_name}'")
