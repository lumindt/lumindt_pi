import psycopg2
import socket
import time
from datetime import datetime


class SQLUploader:
    def __init__(self, dbname="test_data", user="postgres", password="Lumindt2themoon",
                 host="192.168.1.83", port="5432", test_id=None, table_name="L1_5_measurements"):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.table_name = table_name
        self.pi_id = socket.gethostname()
        self.conn = None
        self.cur = None

        # Automatically create unique test_id if not provided
        self.test_id = test_id or f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"[SQL] Using test_id: {self.test_id}")

        self.connect()

    # -------------------------------------------------------------------
    def connect(self):
        """Establish connection to PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            self.conn.autocommit = True
            self.cur = self.conn.cursor()
            print(f"[SQL] Connected to {self.dbname}@{self.host}")
        except Exception as e:
            print(f"[SQL] Connection failed: {e}")
            self.conn = None

    # -------------------------------------------------------------------
    def close(self):
        """Safely close SQL connection."""
        try:
            if self.cur:
                self.cur.close()
            if self.conn:
                self.conn.close()
            print("[SQL] Connection closed.")
        except Exception:
            pass

    # -------------------------------------------------------------------
    def upload_row(self, el_data, fc_data, st_data, test_id=None):
        """Upload one combined data row to SQL database."""
        if not self.conn:
            self.connect()
            if not self.conn:
                print("[SQL] No connection — upload skipped.")
                return

        try:
            ts = time.time()

            # --- Map data to SQL columns ---
            values = {
                # Storage system
                "vessel1_pressure": st_data.get("V1P", None),
                "vessel2_pressure": st_data.get("V2P", None),
                "fc_upstream_pressure": st_data.get("FCP", None),
                "el_output_pressure": st_data.get("ELP", None),
                "v1_t1": st_data.get("V1T1", None),
                "v1_t2": st_data.get("V1T2", None),
                "v1_t3": st_data.get("V1T3", None),
                "v1_t4": st_data.get("V1T4", None),

                # Electrolyzer system
                "el_alicat_output": st_data.get("volumetric_flow_slpm", None),

                # Fuel cell section
                "fc_voltage": fc_data.get("fc_voltage_V", 0.0),
                "fc_power_actual": fc_data.get("fc_power_kW", 0.0),
                "fc_power_setpoint": fc_data.get("fc_target_power_kW", 0.0),

                # Electrolyzer channels 1–8
                **{f"el_measured_production_rate_{i}": el_data.get(f"E{i}_flow_NLh", None)
                   for i in range(1, 9)},
                **{f"el_voltage_{i}": el_data.get(f"E{i}_voltage", None)
                   for i in range(1, 9)},
                **{f"el_current_{i}": el_data.get(f"E{i}_current", None)
                   for i in range(1, 9)},
                **{f"el_power_{i}": el_data.get(f"E{i}_power_kW", None)
                   for i in range(1, 9)},
                **{f"el_status_{i}": 1 if "Idle" not in str(el_data.get(f"E{i}_state", "")) else 0
                   for i in range(1, 9)},
                **{f"el_setpoint_{i}": el_data.get(f"E{i}_prod_rate_pct", None)
                   for i in range(1, 9)},
            }

            # --- Build SQL INSERT query ---
            columns = ["pi_id", "test_id", "ts"] + list(values.keys())
            placeholders = ["%s", "%s", "to_timestamp(%s)"] + ["%s"] * len(values)
            query = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)});"

            data = [self.pi_id, test_id or self.test_id, ts] + list(values.values())

            self.cur.execute(query, data)
            print(f"[SQL] Row inserted for test_id='{test_id or self.test_id}'.")
        except Exception as e:
            print(f"[SQL] Upload error: {e}")
            try:
                self.connect()
            except Exception:
                pass
