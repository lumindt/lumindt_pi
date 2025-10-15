import psycopg2
import random
import time
import socket

conn = psycopg2.connect(dbname="test_data", user="postgres", password="Lumindt2themoon", host="10.1.10.12", port="5432") #PostgreSQL Connection
conn.autocommit = True
cur = conn.cursor()

pi_id = socket.gethostname()
ts = time.time()
test_id = "test_001"   # <-- you can change this per run 

#Randomized data for now
values = {
    # Vessel 1
    "vessel1_pressure": random.uniform(1, 3),
    "v1_t1": random.uniform(20, 30),
    "v1_t2": random.uniform(20, 30),
    "v1_t3": random.uniform(20, 30),
    "v1_t4": random.uniform(20, 30),
    "v1_strain1": random.uniform(0, 1000),
    "v1_strain2": random.uniform(0, 1000),
    "v1_strain3": random.uniform(0, 1000),
    "v1_strain4": random.uniform(0, 1000),

    # Vessel 2
    "vessel2_pressure": random.uniform(1, 3),
    "v2_t1": random.uniform(20, 30),
    "v2_t2": random.uniform(20, 30),
    "v2_t3": random.uniform(20, 30),
    "v2_t4": random.uniform(20, 30),
    "v2_strain1": random.uniform(0, 1000),
    "v2_strain2": random.uniform(0, 1000),
    "v2_strain3": random.uniform(0, 1000),
    "v2_strain4": random.uniform(0, 1000),

    # Fuel Cell
    "fc_upstream_pressure": random.uniform(1, 2),
    "fc_inlet_pressure": random.uniform(0.8, 1.5),
    "fc_voltage": random.uniform(40, 60),
    "fc_amperage": random.uniform(1, 10),
    "fc_power_setpoint": random.uniform(200, 1000),
    "fc_power_actual": random.uniform(200, 1000),
    "fc_consumption_rate": random.uniform(0.1, 1.0),

    # Electrolyzer (System)
    "el_output_pressure": random.uniform(1, 2),
    "el_alicat_output": random.uniform(0.5, 1.5),

    # EL Channel 1
    "el_measured_production_rate_1": random.uniform(0, 100),
    "el_setpoint_1": random.uniform(0, 100),
    "el_status_1": random.choice([0, 1]),
    "el_voltage_1": random.uniform(1, 5),
    "el_current_1": random.uniform(0.1, 10),
    "el_power_1": random.uniform(1, 5) * random.uniform(0.1, 10),
    "el_code_1": random.randint(100, 999),

    # EL Channel 2
    "el_measured_production_rate_2": random.uniform(0, 100),
    "el_setpoint_2": random.uniform(0, 100),
    "el_status_2": random.choice([0, 1]),
    "el_voltage_2": random.uniform(1, 5),
    "el_current_2": random.uniform(0.1, 10),
    "el_power_2": random.uniform(1, 5) * random.uniform(0.1, 10),
    "el_code_2": random.randint(100, 999),

    # EL Channel 3
    "el_measured_production_rate_3": random.uniform(0, 100),
    "el_setpoint_3": random.uniform(0, 100),
    "el_status_3": random.choice([0, 1]),
    "el_voltage_3": random.uniform(1, 5),
    "el_current_3": random.uniform(0.1, 10),
    "el_power_3": random.uniform(1, 5) * random.uniform(0.1, 10),
    "el_code_3": random.randint(100, 999),

    # EL Channel 4
    "el_measured_production_rate_4": random.uniform(0, 100),
    "el_setpoint_4": random.uniform(0, 100),
    "el_status_4": random.choice([0, 1]),
    "el_voltage_4": random.uniform(1, 5),
    "el_current_4": random.uniform(0.1, 10),
    "el_power_4": random.uniform(1, 5) * random.uniform(0.1, 10),
    "el_code_4": random.randint(100, 999),

    # EL Channel 5
    "el_measured_production_rate_5": random.uniform(0, 100),
    "el_setpoint_5": random.uniform(0, 100),
    "el_status_5": random.choice([0, 1]),
    "el_voltage_5": random.uniform(1, 5),
    "el_current_5": random.uniform(0.1, 10),
    "el_power_5": random.uniform(1, 5) * random.uniform(0.1, 10),
    "el_code_5": random.randint(100, 999),

    # EL Channel 6
    "el_measured_production_rate_6": random.uniform(0, 100),
    "el_setpoint_6": random.uniform(0, 100),
    "el_status_6": random.choice([0, 1]),
    "el_voltage_6": random.uniform(1, 5),
    "el_current_6": random.uniform(0.1, 10),
    "el_power_6": random.uniform(1, 5) * random.uniform(0.1, 10),
    "el_code_6": random.randint(100, 999),

    # EL Channel 7
    "el_measured_production_rate_7": random.uniform(0, 100),
    "el_setpoint_7": random.uniform(0, 100),
    "el_status_7": random.choice([0, 1]),
    "el_voltage_7": random.uniform(1, 5),
    "el_current_7": random.uniform(0.1, 10),
    "el_power_7": random.uniform(1, 5) * random.uniform(0.1, 10),
    "el_code_7": random.randint(100, 999),

    # EL Channel 8
    "el_measured_production_rate_8": random.uniform(0, 100),
    "el_setpoint_8": random.uniform(0, 100),
    "el_status_8": random.choice([0, 1]),
    "el_voltage_8": random.uniform(1, 5),
    "el_current_8": random.uniform(0.1, 10),
    "el_power_8": random.uniform(1, 5) * random.uniform(0.1, 10),
    "el_code_8": random.randint(100, 999),
}

#Build Insert Query
columns = ["pi_id", "test_id", "ts"] + list(values.keys())
placeholders = ["%s", "%s", "to_timestamp(%s)"] + ["%s"] * len(values)
query = f"INSERT INTO L1_5_measurements ({', '.join(columns)}) VALUES ({', '.join(placeholders)});"
data = [pi_id, test_id, ts] + list(values.values())

#Insert the data
cur.execute(query, data)
print(f"Inserted row for test_id='{test_id}' successfully!")
cur.close()
conn.close()
