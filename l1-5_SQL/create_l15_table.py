import psycopg2

conn = psycopg2.connect(dbname="test_data", user="postgres", password="Lumindt2themoon", host="10.1.10.12", port="5432") # Database connection
conn.autocommit = True
cur = conn.cursor()

table_name = "L1_5_measurements"
cur.execute(f"DROP TABLE IF EXISTS {table_name};") # Drop if exists for clean slate

cur.execute(f"""
CREATE TABLE {table_name} (
    id SERIAL PRIMARY KEY,
    pi_id TEXT NOT NULL,
    test_id TEXT,                    -- added test_id for grouping runs
    ts TIMESTAMPTZ DEFAULT now(),

    -- Vessel 1
    vessel1_pressure DOUBLE PRECISION,
    v1_t1 DOUBLE PRECISION,
    v1_t2 DOUBLE PRECISION,
    v1_t3 DOUBLE PRECISION,
    v1_t4 DOUBLE PRECISION,
    v1_strain1 DOUBLE PRECISION,
    v1_strain2 DOUBLE PRECISION,
    v1_strain3 DOUBLE PRECISION,
    v1_strain4 DOUBLE PRECISION,

    -- Vessel 2
    vessel2_pressure DOUBLE PRECISION,
    v2_t1 DOUBLE PRECISION,
    v2_t2 DOUBLE PRECISION,
    v2_t3 DOUBLE PRECISION,
    v2_t4 DOUBLE PRECISION,
    v2_strain1 DOUBLE PRECISION,
    v2_strain2 DOUBLE PRECISION,
    v2_strain3 DOUBLE PRECISION,
    v2_strain4 DOUBLE PRECISION,

    -- Fuel Cell
    fc_upstream_pressure DOUBLE PRECISION,
    fc_inlet_pressure DOUBLE PRECISION,
    fc_voltage DOUBLE PRECISION,
    fc_amperage DOUBLE PRECISION,
    fc_power_setpoint DOUBLE PRECISION,
    fc_power_actual DOUBLE PRECISION,
    fc_consumption_rate DOUBLE PRECISION,

    -- Electrolyzer
    el_output_pressure DOUBLE PRECISION,
    el_alicat_output DOUBLE PRECISION,

    -- EL channels 1–8
    el_measured_production_rate_1 DOUBLE PRECISION,
    el_measured_production_rate_2 DOUBLE PRECISION,
    el_measured_production_rate_3 DOUBLE PRECISION,
    el_measured_production_rate_4 DOUBLE PRECISION,
    el_measured_production_rate_5 DOUBLE PRECISION,
    el_measured_production_rate_6 DOUBLE PRECISION,
    el_measured_production_rate_7 DOUBLE PRECISION,
    el_measured_production_rate_8 DOUBLE PRECISION,

    el_setpoint_1 DOUBLE PRECISION,
    el_setpoint_2 DOUBLE PRECISION,
    el_setpoint_3 DOUBLE PRECISION,
    el_setpoint_4 DOUBLE PRECISION,
    el_setpoint_5 DOUBLE PRECISION,
    el_setpoint_6 DOUBLE PRECISION,
    el_setpoint_7 DOUBLE PRECISION,
    el_setpoint_8 DOUBLE PRECISION,

    el_status_1 DOUBLE PRECISION,
    el_status_2 DOUBLE PRECISION,
    el_status_3 DOUBLE PRECISION,
    el_status_4 DOUBLE PRECISION,
    el_status_5 DOUBLE PRECISION,
    el_status_6 DOUBLE PRECISION,
    el_status_7 DOUBLE PRECISION,
    el_status_8 DOUBLE PRECISION,

    el_voltage_1 DOUBLE PRECISION,
    el_voltage_2 DOUBLE PRECISION,
    el_voltage_3 DOUBLE PRECISION,
    el_voltage_4 DOUBLE PRECISION,
    el_voltage_5 DOUBLE PRECISION,
    el_voltage_6 DOUBLE PRECISION,
    el_voltage_7 DOUBLE PRECISION,
    el_voltage_8 DOUBLE PRECISION,

    el_current_1 DOUBLE PRECISION,
    el_current_2 DOUBLE PRECISION,
    el_current_3 DOUBLE PRECISION,
    el_current_4 DOUBLE PRECISION,
    el_current_5 DOUBLE PRECISION,
    el_current_6 DOUBLE PRECISION,
    el_current_7 DOUBLE PRECISION,
    el_current_8 DOUBLE PRECISION,

    el_power_1 DOUBLE PRECISION,
    el_power_2 DOUBLE PRECISION,
    el_power_3 DOUBLE PRECISION,
    el_power_4 DOUBLE PRECISION,
    el_power_5 DOUBLE PRECISION,
    el_power_6 DOUBLE PRECISION,
    el_power_7 DOUBLE PRECISION,
    el_power_8 DOUBLE PRECISION,

    el_code_1 DOUBLE PRECISION,
    el_code_2 DOUBLE PRECISION,
    el_code_3 DOUBLE PRECISION,
    el_code_4 DOUBLE PRECISION,
    el_code_5 DOUBLE PRECISION,
    el_code_6 DOUBLE PRECISION,
    el_code_7 DOUBLE PRECISION,
    el_code_8 DOUBLE PRECISION
);
""")

print(f"Table '{table_name}' created successfully.")
cur.close()
conn.close()
