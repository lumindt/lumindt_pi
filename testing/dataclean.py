import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

# === Load your data ===
# Replace with your file path and column names
file_path = 'resistance_data.xlsx'  # e.g., 'data.xlsx' for Excel
df = pd.read_excel(file_path)  # or pd.read_excel(file_path)

# Inspect your columns
print(df.head())

# === Adjust these to your columns ===
x_col = 'time_sec'   # replace with your X column name
y_col = 'R_var'   # replace with your Y column name

# === Define the cutoff range for the linear portion ===
# Example: keep only X values greater than 8
linear_df = df[df[x_col] > 8]

# === Perform linear regression ===
slope, intercept, r_value, p_value, std_err = linregress(
    linear_df[x_col],
    linear_df[y_col]
)

print(f"Slope: {slope}")
print(f"Intercept: {intercept}")
print(f"Equation: y = {slope:.3f} * x + {intercept:.3f}")

# === Plot original data and the linear portion with the fit ===
plt.figure(figsize=(10, 6))
plt.scatter(df[x_col], df[y_col], label='Original Data', alpha=0.5)
plt.scatter(linear_df[x_col], linear_df[y_col], label='Linear Portion', color='orange')

# Plot best-fit line
x_fit = np.linspace(linear_df[x_col].min(), linear_df[x_col].max(), 100)
y_fit = slope * x_fit + intercept
plt.plot(x_fit, y_fit, 'r-', label=f'Best Fit: y = {slope:.2f}x + {intercept:.2f}')

plt.xlabel(x_col)
plt.ylabel(y_col)
plt.xscale('log')

plt.legend()
plt.title('Linear Portion with Best Fit Line')
plt.grid(True)
plt.show()
plt.savefig('linear_fit_plot.png', dpi=300)  # Saves as PNG with 300 dpi
print("Plot saved as 'linear_fit_plot.png'")
# === Save the isolated linear data ===
linear_df.to_csv('linear_portion.csv', index=False)
print("Saved linear portion to 'linear_portion.csv'")
