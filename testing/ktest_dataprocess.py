import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

from openpyxl import load_workbook

# === Constants ===
ALPHA = 0.00385
LENGTH = 0.06  # Length of the wire in meters

# === Paths ===
input_file = 'resistance_data.xlsx'
output_dir = 'plots'
processed_file = 'processed_data.xlsx'

os.makedirs(output_dir, exist_ok=True)

# === Load workbook ===
xls = pd.ExcelFile(input_file)

# === Store processed sheets ===
processed_sheets = {}

for sheet_name in xls.sheet_names:
    print(f'Processing sheet: {sheet_name}')
    df = pd.read_excel(xls, sheet_name=sheet_name)
    df.columns = df.columns.str.strip()  # Remove any accidental spaces

    print(df.columns)

    # --- Get smallest positive R_var ---
    R0 = df[df['R_var'] > 0]['R_var'].min()

    # --- Remove rows with negative R_var ---
    df = df[df['R_var'] > 0].copy()

    # --- Calculate averages ---
    R_var_avg = df['R_var'].mean()
    V_out_avg = df['Voltage (V)'].mean()

    # --- Calculate other constants ---
    Rtot = 2 * 10 * (10 + R_var_avg) / (3 * 10 + R_var_avg)
    i1 = 0.5 * ((3.3 / Rtot) - (V_out_avg / 10))
    P = i1 ** 2 * R_var_avg
    q_dot = P / LENGTH  # Watts per meter

    # --- Add delT column ---
    df['delT'] = (1 / ALPHA) * (df['R_var'] / R0 - 1)

    # --- Remove outliers ---
    df = df[df['delT'] < df['delT'].quantile(0.99)]

    # --- Fit best line ---
    x = df['time_sec']
    y = df['delT']
    log_x = np.log(x)
    m, b = np.polyfit(log_x, y, 1)

    # --- Calculate k ---
    k = q_dot / (4 * np.pi * m)

    print(f'Calculated slope m: {m:.4f}')
    print(f'Calculated k: {k:.4f} W/(m·K)')

    # --- Scatter plot ---
    plt.figure(figsize=(8, 6))
    plt.scatter(x, y, label='Data', s=20)
    plt.xscale('log')

    x_sorted = np.sort(x)
    y_fit = m * np.log(x_sorted) + b
    plt.plot(x_sorted, y_fit, color='red', label=f'Best Fit: y = {m:.4f} * log(x) + {b:.4f}')

    plt.xlabel('Time (sec, log scale)')
    plt.ylabel('delT')
    plt.title(f'delT vs Time for {sheet_name}')
    plt.legend()
    plt.tight_layout()

    plot_filename = os.path.join(output_dir, f'{sheet_name}_plot.png')
    plt.savefig(plot_filename)
    plt.close()
    print(f'Plot saved to: {plot_filename}')

    # --- Save constants + processed data to new DataFrame ---
    # Build constants as single-row DataFrame
    consts = pd.DataFrame({
        'Constant': [
            'alpha', 'R0', 'R_var_avg', 'V_out_avg',
            'Rtot', 'i1', 'P', 'q_dot', 'm', 'k'
        ],
        'Value': [
            ALPHA, R0, R_var_avg, V_out_avg,
            Rtot, i1, P, q_dot, m, k
        ]
    })

    # Add an empty row as spacer
    spacer = pd.DataFrame([['', '']], columns=['Constant', 'Value'])

    # Combine: constants, spacer, then processed data
    df_reset = df.reset_index(drop=True)
    combined = pd.concat([consts, spacer, df_reset], ignore_index=True)

    processed_sheets[sheet_name] = combined

# === Write all sheets to one Excel ===
with pd.ExcelWriter(processed_file) as writer:
    for name, processed_df in processed_sheets.items():
        processed_df.to_excel(writer, sheet_name=name, index=False)

print(f'\nProcessed data written to: {processed_file}')
