import psycopg2
import pandas as pd
from tabulate import tabulate

conn = psycopg2.connect(dbname="test_data", user="postgres", password="Lumindt2themoon", host="10.1.10.12", port="5432") # Database connection
df = pd.read_sql("SELECT * FROM L1_5_measurements ORDER BY ts DESC LIMIT 50;", conn) # Load table into pandas

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

df_el8 = df[el8_cols] # Filter dataframe to just those columns

print("Electrolyzer Channel 8 Data (latest 10 rows):")
print(tabulate(df_el8.head(10), headers="keys", tablefmt="fancy_grid", showindex=False))
conn.close()
