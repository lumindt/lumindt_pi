import psycopg2

conn = psycopg2.connect(dbname="test_data", user="postgres", password="Lumindt2themoon", host="10.1.10.12", port="5432") # Database connection
conn.autocommit = True
cur = conn.cursor()

table_name = "L15_V2"
cur.execute(f"DROP TABLE IF EXISTS {table_name};") # Drop if exists for clean slate

cur.execute(f"""
CREATE TABLE {table_name} (
    id SERIAL PRIMARY KEY,
    pi_id TEXT NOT NULL,
    test_id TEXT,                    -- added test_id for grouping runs
    ts TIMESTAMPTZ DEFAULT now(),

    -- Storage
    rtemp DOUBLE PRECISION,         -- Reference Temperature Sensor
    el_pt DOUBLE PRECISION,         -- Electrolyzer Pressure Transducer
    fc_pt DOUBLE PRECISION,         -- Fuel Cell Pressure Transducer
    mflow DOUBLE PRECISION,         -- H2 Flow Rate
    
    -- Vessel 1
    v1_pt DOUBLE PRECISION,         -- Vessel 1 Pressure Transducer
    v1_t1 DOUBLE PRECISION,         -- Vessel 1 Temperature Sensor 1 
    v1_t2 DOUBLE PRECISION,         -- Vessel 1 Temperature Sensor 2
    v1_t3 DOUBLE PRECISION,         -- Vessel 1 Temperature Sensor 3
    v1_t4 DOUBLE PRECISION,         -- Vessel 1 Temperature Sensor 4
    v1_s1 DOUBLE PRECISION,         -- Vessel 1 Strain Gauge 1
    v1_s2 DOUBLE PRECISION,         -- Vessel 1 Strain Gauge 2
    v1_s3 DOUBLE PRECISION,         -- Vessel 1 Strain Gauge 3
    v1_s4 DOUBLE PRECISION,         -- Vessel 1 Strain Gauge 4
    v1_vi DOUBLE PRECISION,         -- Vessel 1 Inlet Valve Status
    v1_vo DOUBLE PRECISION,         -- Vessel 1 Outlet Valve Status

    -- Vessel 2
    v2_pt DOUBLE PRECISION,         -- Vessel 2 Pressure Transducer
    v2_t1 DOUBLE PRECISION,         -- Vessel 2 Temperature Sensor 1
    v2_t2 DOUBLE PRECISION,         -- Vessel 2 Temperature Sensor 2
    v2_t3 DOUBLE PRECISION,         -- Vessel 2 Temperature Sensor 3
    v2_t4 DOUBLE PRECISION,         -- Vessel 2 Temperature Sensor 4
    v2_s1 DOUBLE PRECISION,         -- Vessel 2 Strain Gauge 1
    v2_s2 DOUBLE PRECISION,         -- Vessel 2 Strain Gauge 2
    v2_s3 DOUBLE PRECISION,         -- Vessel 2 Strain Gauge 3
    v2_s4 DOUBLE PRECISION,         -- Vessel 2 Strain Gauge 4
    v2_vi DOUBLE PRECISION,         -- Vessel 2 Inlet Valve Status
    v2_vo DOUBLE PRECISION,         -- Vessel 2 Outlet Valve Status

    -- Fuel Cell
        -- Commands
    fc_on DOUBLE PRECISION,         -- Fuel Cell On/Off State
    fc_v_cmd DOUBLE PRECISION,      -- Fuel Cell Voltage Command
    fc_p_cmd DOUBLE PRECISION,      -- Fuel Cell Power Command
        -- Measurements
    fc_phase DOUBLE PRECISION,      -- Fuel Cell Phase
    fc_fault DOUBLE PRECISION,      -- Fuel Cell Fault Code
    fc_p_max DOUBLE PRECISION,      -- Fuel Cell Max Power
    fc_p_sys DOUBLE PRECISION,      -- Fuel Cell System Power
    fc_i_sys DOUBLE PRECISION,      -- Fuel Cell System Current
    fc_v_sys DOUBLE PRECISION,      -- Fuel Cell System Voltage
    fc_p_stk DOUBLE PRECISION,      -- Fuel Cell Stack Power
    fc_i_stk DOUBLE PRECISION,      -- Fuel Cell Stack Current
    fc_v_stk DOUBLE PRECISION,      -- Fuel Cell Stack Voltage

    -- Electrolyzer Modules
        -- Commands
    el1_on DOUBLE PRECISION,        -- Electrolyzer 1 On/Off State
    el2_on DOUBLE PRECISION,        -- Electrolyzer 2 On/Off State
    el3_on DOUBLE PRECISION,        -- Electrolyzer 3 On/Off State
    el4_on DOUBLE PRECISION,        -- Electrolyzer 4 On/Off State
    el5_on DOUBLE PRECISION,        -- Electrolyzer 5 On/Off State
    el6_on DOUBLE PRECISION,        -- Electrolyzer 6 On/Off State
    el7_on DOUBLE PRECISION,        -- Electrolyzer 7 On/Off State
    el8_on DOUBLE PRECISION,        -- Electrolyzer 8 On/Off State
    el1_pcnt DOUBLE PRECISION,      -- Electrolyzer 1 Production Rate %
    el2_pcnt DOUBLE PRECISION,      -- Electrolyzer 2 Production Rate %
    el3_pcnt DOUBLE PRECISION,      -- Electrolyzer 3 Production Rate %
    el4_pcnt DOUBLE PRECISION,      -- Electrolyzer 4 Production Rate %
    el5_pcnt DOUBLE PRECISION,      -- Electrolyzer 5 Production Rate %
    el6_pcnt DOUBLE PRECISION,      -- Electrolyzer 6 Production Rate %
    el7_pcnt DOUBLE PRECISION,      -- Electrolyzer 7 Production Rate %
    el8_pcnt DOUBLE PRECISION,      -- Electrolyzer 8 Production Rate %
        -- Measurements
    el1_state DOUBLE PRECISION,     -- Electrolyzer 1 State
    el2_state DOUBLE PRECISION,     -- Electrolyzer 2 State
    el3_state DOUBLE PRECISION,     -- Electrolyzer 3 State
    el4_state DOUBLE PRECISION,     -- Electrolyzer 4 State
    el5_state DOUBLE PRECISION,     -- Electrolyzer 5 State
    el6_state DOUBLE PRECISION,     -- Electrolyzer 6 State
    el7_state DOUBLE PRECISION,     -- Electrolyzer 7 State
    el8_state DOUBLE PRECISION,     -- Electrolyzer 8 State
    el1_warn DOUBLE PRECISION,      -- Electrolyzer 1 Warning Code
    el2_warn DOUBLE PRECISION,      -- Electrolyzer 2 Warning Code
    el3_warn DOUBLE PRECISION,      -- Electrolyzer 3 Warning Code
    el4_warn DOUBLE PRECISION,      -- Electrolyzer 4 Warning Code
    el5_warn DOUBLE PRECISION,      -- Electrolyzer 5 Warning Code
    el6_warn DOUBLE PRECISION,      -- Electrolyzer 6 Warning Code
    el7_warn DOUBLE PRECISION,      -- Electrolyzer 7 Warning Code
    el8_warn DOUBLE PRECISION,      -- Electrolyzer 8 Warning Code
    el1_error DOUBLE PRECISION,     -- Electrolyzer 1 Error Code
    el2_error DOUBLE PRECISION,     -- Electrolyzer 2 Error Code
    el3_error DOUBLE PRECISION,     -- Electrolyzer 3 Error Code
    el4_error DOUBLE PRECISION,     -- Electrolyzer 4 Error Code
    el5_error DOUBLE PRECISION,     -- Electrolyzer 5 Error Code
    el6_error DOUBLE PRECISION,     -- Electrolyzer 6 Error Code
    el7_error DOUBLE PRECISION,     -- Electrolyzer 7 Error Code
    el8_error DOUBLE PRECISION,     -- Electrolyzer 8 Error Code
    el1_flow DOUBLE PRECISION,      -- Electrolyzer 1 Measured H2 Flow Rate
    el2_flow DOUBLE PRECISION,      -- Electrolyzer 2 Measured H2 Flow Rate
    el3_flow DOUBLE PRECISION,      -- Electrolyzer 3 Measured H2 Flow Rate
    el4_flow DOUBLE PRECISION,      -- Electrolyzer 4 Measured H2 Flow Rate
    el5_flow DOUBLE PRECISION,      -- Electrolyzer 5 Measured H2 Flow Rate
    el6_flow DOUBLE PRECISION,      -- Electrolyzer 6 Measured H2 Flow Rate
    el7_flow DOUBLE PRECISION,      -- Electrolyzer 7 Measured H2 Flow Rate
    el8_flow DOUBLE PRECISION,      -- Electrolyzer 8 Measured H2 Flow Rate
    el1_volt DOUBLE PRECISION,      -- Electrolyzer 1 Voltage
    el2_volt DOUBLE PRECISION,      -- Electrolyzer 2 Voltage
    el3_volt DOUBLE PRECISION,      -- Electrolyzer 3 Voltage
    el4_volt DOUBLE PRECISION,      -- Electrolyzer 4 Voltage
    el5_volt DOUBLE PRECISION,      -- Electrolyzer 5 Voltage
    el6_volt DOUBLE PRECISION,      -- Electrolyzer 6 Voltage
    el7_volt DOUBLE PRECISION,      -- Electrolyzer 7 Voltage
    el8_volt DOUBLE PRECISION,      -- Electrolyzer 8 Voltage
    el1_curr DOUBLE PRECISION,      -- Electrolyzer 1 Current
    el2_curr DOUBLE PRECISION,      -- Electrolyzer 2 Current
    el3_curr DOUBLE PRECISION,      -- Electrolyzer 3 Current
    el4_curr DOUBLE PRECISION,      -- Electrolyzer 4 Current
    el5_curr DOUBLE PRECISION,      -- Electrolyzer 5 Current
    el6_curr DOUBLE PRECISION,      -- Electrolyzer 6 Current
    el7_curr DOUBLE PRECISION,      -- Electrolyzer 7 Current
    el8_curr DOUBLE PRECISION,      -- Electrolyzer 8 Current
    el1_pow DOUBLE PRECISION,       -- Electrolyzer 1 Power
    el2_pow DOUBLE PRECISION,       -- Electrolyzer 2 Power
    el3_pow DOUBLE PRECISION,       -- Electrolyzer 3 Power
    el4_pow DOUBLE PRECISION,       -- Electrolyzer 4 Power
    el5_pow DOUBLE PRECISION,       -- Electrolyzer 5 Power
    el6_pow DOUBLE PRECISION,       -- Electrolyzer 6 Power
    el7_pow DOUBLE PRECISION,       -- Electrolyzer 7 Power
    el8_pow DOUBLE PRECISION,       -- Electrolyzer 8 Power
        -- Totals
    elt_flow DOUBLE PRECISION,      -- Total Electrolyzer H2 Flow Rate
    elt_pow DOUBLE PRECISION,       -- Total Electrolyzer Power
        -- Dryer
    dy1_on DOUBLE PRECISION,        -- Dryer 1 On/Off State
    dy2_on DOUBLE PRECISION,        -- Dryer 2 On/Off State
    dy1_state DOUBLE PRECISION,     -- Dryer 1 State
    dy2_state DOUBLE PRECISION,     -- Dryer 2 State
    dy1_warn DOUBLE PRECISION,      -- Dryer 1 Warning Code
    dy2_warn DOUBLE PRECISION,      -- Dryer 2 Warning Code
    dy1_error DOUBLE PRECISION,     -- Dryer 1 Error Code
    dy2_error DOUBLE PRECISION,     -- Dryer 2 Error Code
    dy1_pi DOUBLE PRECISION,        -- Dryer 1 Inlet Pressure
    dy2_pi DOUBLE PRECISION,        -- Dryer 2 Inlet Pressure
    dy1_po DOUBLE PRECISION,        -- Dryer 1 Outlet Pressure
    dy2_po DOUBLE PRECISION,        -- Dryer 2 Outlet Pressure
        -- Water Tank
    wt_state DOUBLE PRECISION,      -- Water Tank State
    wt_level DOUBLE PRECISION       -- Water Tank Level
);
""")

print(f"Table '{table_name}' created successfully.")
cur.close()
conn.close()
