import psycopg2
import pandas as pd
from matplotlib import pyplot as plt

# ------------------------------------------------------------
# Database connection
# ------------------------------------------------------------
conn = psycopg2.connect(
    dbname="test_data",
    user="postgres",
    password="Lumindt2themoon",
    host="10.1.10.12",
    port="5432"
)

# Load recent rows
df = pd.read_sql("SELECT * FROM L1_5_measurements ORDER BY ts DESC LIMIT 50;", conn)

# ------------------------------------------------------------
# Electrolyzer Channel 8 summary
# ------------------------------------------------------------
el8_cols = [
    "ts", "pi_id", "test_id",
    "el_measured_production_rate_8",
    "el_setpoint_8",
    "el_status_8",
    "el_voltage_8",
    "el_current_8",
    "el_power_8",
    "el_code_8"
]

df_el8 = df[el8_cols]

# ------------------------------------------------------------
# Fuel Cell summary
# ------------------------------------------------------------
fc_cols = [
    "ts", "pi_id", "test_id",
    "fc_voltage",
    "fc_power_actual",
    "fc_power_setpoint",
    "el_alicat_output"
]

df_fc = df[fc_cols]

print("\n=========================== Fuel Cell Data (latest 10 rows) ===========================")
print(tabulate(df_fc.head(10), headers="keys", tablefmt="fancy_grid", showindex=False))

conn.close()
