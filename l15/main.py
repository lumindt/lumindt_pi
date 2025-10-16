import time
import sys
import select
import threading
from datetime import datetime
from math import isnan
from tabulate import tabulate
from enapter.enapter_modbus import ElectrolyzerModbusController
from horizon_fc.FuelCellController import FuelCellController
from horizon_fc.alicat import Controller as AlicatController
import utils
import config
from sql_uploader import SQLUploader

# Starting IP then add 1 for each additional unit
starting_ip = 64
ENAPTER_HOSTS = [f"10.1.10.{starting_ip + i}" for i in range(8)]  # E64–E71
DRYER_HOSTS = [f"10.1.10.{starting_ip}", f"10.1.10.{starting_ip + 4}"]

def safe_read(func, fallback=float("nan")):
    try:
        val = func()
        return val if val is not None else fallback
    except Exception:
        return fallback

def safe_float(val, default=0.0):
    try:
        return float(val) if val is not None else default
    except (ValueError, TypeError):
        return default

class L15System:
    def __init__(self):
        self.mode = "idle"
        self.controllers = {ip: ElectrolyzerModbusController(host=ip) for ip in ENAPTER_HOSTS}
        self.dryers = {ip: ElectrolyzerModbusController(host=ip) for ip in DRYER_HOSTS}
        self.sql_uploader = SQLUploader()
        #require test id if only enter isd pressed
        self.test_id = ""
        while not self.test_id:
            self.test_id = input("Enter SQL test ID (e.g., test_001): ").strip()
            if not self.test_id:
                print("Test ID cannot be empty. Please enter a valid Test ID.")

        self.sql_upload_interval = 10  # seconds between uploads *USER SETTING*
        self._last_sql_upload = 0      # internal timer tracker


        try:
            print("Initializing Alicat controller...")
            self.alicat = AlicatController()
            self.alicat_ready = True
        except Exception as e:
            print(f"[WARN] Alicat init failed: {e}")
            self.alicat_ready = False
            self.alicat = None

        try:
            print("Initializing FuelCellController...")
            self.fuelcell = FuelCellController(debug=False)
            if not getattr(self.fuelcell, "online", True):
                print("[WARN] Fuel cell offline (no CAN detected). Continuing in offline mode.")
        except Exception as e:
            print(f"[WARN] FuelCellController init failed: {e}")
            self.fuelcell = None

    def set_mode(self, mode):
        mode = mode.lower()
        if mode not in ["charge", "discharge", "idle"]:
            print("Invalid mode.")
            return

        self.mode = mode
        print(f"\n=== MODE: {mode.upper()} ===")

        if mode == "charge":
            self.fuelcell.fuelcell_on(False) if self.fuelcell else None
            self.start_dryers()
            self.start_electrolyzers()
            print("[MODE] System is now in CHARGE mode.")

        elif mode == "discharge":
            self.stop_electrolyzers()
            self.stop_dryers()
            if self.fuelcell:
                try:
                    target_power = None
                    while target_power is None:
                        try:
                            user_input = input("Enter desired discharge power (0–10 kW): ").strip()
                            target_power = float(user_input)
                            if not (0 <= target_power <= 10):
                                print("Invalid range.")
                                target_power = None
                        except ValueError:
                            print("Invalid input.")

                    print(f"[FC] Preparing for discharge at {target_power} kW...")
                    self.fuelcell.set_power(target_power)
                    self.fuelcell.set_voltage(54.0)
                    self.fuelcell.fuelcell_on(False)
                    print(f"[FC] Armed (OFF): target 54 V, {target_power} kW. Press 'o' to start.")
                except Exception as e:
                    print(f"[FC] Arm error: {e}")
            else:
                print("[WARN] Fuel cell unavailable.")

        elif mode == "idle":
            self.stop_electrolyzers()
            self.stop_dryers()
            self.fuelcell.fuelcell_on(False) if self.fuelcell else None
            print("[MODE] System is now in IDLE mode.")

    def prompt_mode_change(self):
        """Prompt user for a new mode and apply it via set_mode()."""
        try:
            print("\nAvailable modes: idle | charge | discharge")
            new_mode = input("Enter new mode: ").strip().lower()
            if new_mode not in ["idle", "charge", "discharge"]:
                print("Invalid mode. No change made.")
                return
            if new_mode == self.mode:
                print(f"Already in {self.mode} mode.")
                return
            self.set_mode(new_mode)
        except Exception as e:
            print(f"[MODE] Error switching mode: {e}")

    def start_electrolyzers(self):
        for ctrl in self.controllers.values():
            try:
                ctrl.write_start_electrolyser()
            except Exception as e:
                print(f"[EL] Start error: {e}")
        print("[EL] Electrolyzers started.")

    def stop_electrolyzers(self):
        for ctrl in self.controllers.values():
            try:
                ctrl.write_stop_electrolyser()
            except Exception as e:
                print(f"[EL] Stop error: {e}")
        print("[EL] Electrolyzers stopped.")

    def stop_fuelcell(self):
        if self.fuelcell:
            try:
                self.fuelcell.fuelcell_on(False)
                print("[FC] Fuel cell turned OFF.")
            except Exception as e:
                print(f"[FC] OFF error: {e}")
        else:
            print("[FC] Fuel cell unavailable.")

    def start_dryers(self):
        """Start both dryers."""
        for d in self.dryers.values():
            try:
                d.write_start_dryer()
            except Exception as e:
                print(f"[DRYER] Start error: {e}")
        print("[DRYER] Start command sent.")

    def stop_dryers(self):
        """Stop both dryers."""
        for d in self.dryers.values():
            try:
                d.write_stop_dryer()
            except Exception as e:
                print(f"[DRYER] Stop error: {e}")
        print("[DRYER] Stop command sent.")

    def read_dryer_states(self):
        rows = []
        for idx, (ip, ctrl) in enumerate(self.dryers.items(), start=1):
            state_code = safe_read(ctrl.display_dryer_state, fallback=0)
            state_desc = config.DRYER_STATES.get(state_code, f"Unknown ({state_code})")
            rows.append([idx, ip, state_desc])
        return rows

    def format_dryer_table(self, rows):
        if not rows:
            return "[No dryer data available]"
        return tabulate(rows, headers=["#", "IP", "Dryer State"], tablefmt="fancy_grid")

    def read_electrolyzer_data(self):
        data = {}
        total_flow, total_power = 0.0, 0.0
        for idx, (ip, ctrl) in enumerate(self.controllers.items(), start=1):
            voltage = safe_read(ctrl.display_stack_voltage)
            current = safe_read(ctrl.display_stack_current)
            power = (voltage * current) / 1000 if not isnan(voltage) and not isnan(current) else float("nan")
            flow = safe_read(ctrl.display_stack_H2_flow_rate)
            prod_rate = safe_read(ctrl.display_production_rate)
            temp = safe_read(ctrl.display_electrolyte_temperature)
            state = safe_read(ctrl.display_electrolyser_state, "Unknown")

            if not isnan(flow):
                total_flow += flow
            if not isnan(power):
                total_power += power

            data[f"E{idx}_ip"] = ip
            data[f"E{idx}_state"] = state
            data[f"E{idx}_voltage"] = voltage
            data[f"E{idx}_current"] = current
            data[f"E{idx}_power_kW"] = power
            data[f"E{idx}_flow_NLh"] = flow
            data[f"E{idx}_prod_rate_pct"] = prod_rate
            data[f"E{idx}_temp_C"] = temp

        data["total_flow_NLh"] = total_flow
        data["total_power_kW"] = total_power
        return data

    def read_fuelcell_block(self):
        if not self.fuelcell:
            return dict(fc_power_kW=0, fc_voltage_V=0, fc_target_power_kW=0, fc_target_voltage_V=0, fc_phase="N/A", fc_faults=[])
        fc_power = safe_float(self.fuelcell.get_fc_power())
        fc_voltage = safe_float(self.fuelcell.get_system_output_voltage())
        fc_target_power = safe_float(self.fuelcell.get_target_power())
        fc_target_voltage = safe_float(self.fuelcell.get_target_voltage())
        fc_phase = self.fuelcell.get_phase() or "N/A"
        fc_faults = self.fuelcell.get_fault_codes() or []
        return dict(fc_power_kW=fc_power, fc_voltage_V=fc_voltage,
                    fc_target_power_kW=fc_target_power, fc_target_voltage_V=fc_target_voltage,
                    fc_phase=fc_phase, fc_faults=fc_faults)

    def read_alicat_data(self):
        if not self.alicat_ready or not self.alicat:
            return {"mass_flow_gps": -1.0, "volumetric_flow_slpm": -1.0}
        try:
            data = self.alicat.poll()
            return {"mass_flow_gps": data.get("M", -1.0), "volumetric_flow_slpm": data.get("V", -1.0)}
        except Exception as e:
            print(f"[WARN] Alicat read failed: {e}")
            return {"mass_flow_gps": -1.0, "volumetric_flow_slpm": -1.0}

    def format_electrolyzer_table(self, data):
        rows = []
        for i in range(1, 9):
            prefix = f"E{i}_"
            if f"{prefix}ip" in data:
                rows.append([
                    i, data.get(f"{prefix}ip", ""), data.get(f"{prefix}state", ""),
                    round(data.get(f"{prefix}voltage", 0), 3),
                    round(data.get(f"{prefix}current", 0), 3),
                    round(data.get(f"{prefix}power_kW", 0), 5),
                    round(data.get(f"{prefix}flow_NLh", 0), 1),
                    round(data.get(f"{prefix}prod_rate_pct", 0), 1),
                    round(data.get(f"{prefix}temp_C", 0), 1),
                ])
        rows.append(["", "—", "TOTAL", "", "", round(data.get("total_power_kW", 0), 3),
                     round(data.get("total_flow_NLh", 0), 1), ""])
        headers = ["#", "IP", "State", "V (V)", "I (A)", "P (kW)",
                   "Flow (NL/h)", "Prod Rate (%)", "Temp (°C)"]
        return tabulate(rows, headers=headers, tablefmt="fancy_grid")

    def run_loop(self):
        print(f"Running system in {self.mode.upper()} mode. (Press Ctrl+C to exit)")

        latest = {"el": {}, "fc": {}, "al": {}, "dryer": []}
        stop_flag = threading.Event()

        def data_updater():
            while not stop_flag.is_set():
                try:
                    el = self.read_electrolyzer_data()
                    fc = self.read_fuelcell_block()
                    al = self.read_alicat_data()
                    dryers = self.read_dryer_states()
                    latest.update({"el": el, "fc": fc, "al": al, "dryer": dryers})
                except Exception as e:
                    print(f"[DATA_THREAD] {e}")
                time.sleep(1.5)


        threading.Thread(target=data_updater, daemon=True).start()

        try:
            while not stop_flag.is_set():
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Snapshot of latest to avoid thread race
                data_snapshot = latest.copy()
                el = data_snapshot.get("el", {})
                fc = data_snapshot.get("fc", {})
                al = data_snapshot.get("al", {})
                dryers = data_snapshot.get("dryer", [])


                print("\n" + "=" * 70)
                print("\n" + "=" * 70)
                print(f"Timestamp: {now} | Mode: {self.mode.upper()}\n")

                print("ELECTROLYZER STATUS:")
                print(self.format_electrolyzer_table(el))

                print("\nFUEL CELL STATUS:")
                print(tabulate(
                    [[
                        fc.get("fc_phase", "N/A"),
                        round(fc.get("fc_voltage_V", 0), 2),
                        round(fc.get("fc_power_kW", 0), 2),
                        round(fc.get("fc_target_voltage_V", 0), 2),
                        round(fc.get("fc_target_power_kW", 0), 2),
                        round(al.get("mass_flow_gps", 0), 2),
                        round(al.get("volumetric_flow_slpm", 0), 2)
                    ]],
                    headers=["Phase", "Voltage (V)", "Power (kW)", "Target Voltage (V)", "Target Power (kW)",
                             "Mass Flow (g/s)", "Vol Flow (SLPM)"],
                    tablefmt="fancy_grid"
                ))

                print("\nDRYER STATUS:")
                print(self.format_dryer_table(dryers))

                 # Upload to SQL directly (synchronous, easier to debug)
                # --- Upload to SQL every N seconds ---
                if self.sql_uploader:
                    if time.time() - self._last_sql_upload >= self.sql_upload_interval:
                        try:
                            print(f"[SQL] Uploading data at {now} ...", end=" ")
                            self.sql_uploader.upload_row(el, fc, al, self.test_id)
                            print("✅ Done.")
                            self._last_sql_upload = time.time()
                        except Exception as e:
                            print(f"[SQL ERROR] {e}")


                print("=" * 70)

                # Hotkeys
                if self.mode == "idle":
                    print("Hotkeys: 'm' switch mode | 'q' quit")
                elif self.mode == "charge":
                    print("Hotkeys: 'r' set production rate | 'm' switch mode | 'q' quit")
                elif self.mode == "discharge":
                    print("Hotkeys: 'p' set FC power | 'o' FC ON | 'f' FC OFF | 'm' switch mode | 'q' quit")

                try: #Handle keypresses
                    rlist, _, _ = select.select([sys.stdin], [], [], 0)
                except Exception:
                    rlist = []

                if sys.stdin in rlist:
                    try:
                        key = sys.stdin.read(1).strip().lower()
                    except Exception:
                        key = ""

                    if key == "q":
                        print("Exiting system loop...")
                        break
                    elif key == "m":
                        print("\nSwitching mode...")
                        self.prompt_mode_change()
                        time.sleep(0.5)
                        continue
                    elif self.mode == "discharge":
                        if key == "p":
                            try:
                                target = float(input("Enter target power (0–10 kW): ").strip())
                                if 0 <= target <= 10:
                                    if self.fuelcell:
                                        self.fuelcell.set_power(target)
                                    print(f"[FC] Target power set to {target} kW.")
                                else:
                                    print("Invalid power value.")
                            except ValueError:
                                print("Invalid input.")
                        elif key == "o":
                            try:
                                if self.fuelcell:
                                    self.fuelcell.fuelcell_on(True)
                                print("[FC] Fuel cell turned ON.")
                            except Exception as e:
                                print(f"[FC] ON error: {e}")

                        elif key == "f":
                            try:
                                if self.fuelcell:
                                    self.fuelcell.fuelcell_on(False)
                                print("[FC] Fuel cell turned OFF.")
                            except Exception as e:
                                print(f"[FC] OFF error: {e}")

                    elif self.mode == "charge" and key == "r":
                        try:
                            rate = float(input("Enter new target production rate (%): ").strip())
                            if rate < 0:
                                print("Invalid rate.")
                            else:
                                for ctrl in self.controllers.values():
                                    try:
                                        ctrl.write_production_rate(rate)
                                    except Exception as e:
                                        print(f"[EL] Rate set error: {e}")
                                print(f"[EL] Target production rate set to {rate} % for all electrolyzers.")
                        except ValueError:
                            print("Invalid input.")
                time.sleep(1)

        except KeyboardInterrupt:
            print("\nInterrupted by user.")
        except Exception as e:
            print(f"[LOOP] Unexpected error: {e}")
            time.sleep(1)
        finally:
            stop_flag.set()
            print("\nSystem stopping...")
            self.shutdown()

    def shutdown(self):
        print("\nSystem shutdown...")
        self.stop_electrolyzers()
        self.stop_dryers()
        self.fuelcell.fuelcell_on(False) if self.fuelcell else None
        print("System safely stopped.")

if __name__ == "__main__":
    system = L15System()
    try:
        print("Select mode:")
        print("1. Charge (Electrolyzers ON)")
        print("2. Discharge (Fuel Cell ON)")
        print("3. Idle (All OFF)")
        choice = input("Enter choice [1–3]: ").strip()
        system.set_mode("charge" if choice == "1" else "discharge" if choice == "2" else "idle")
        system.run_loop()
    except KeyboardInterrupt: print("\n[CTRL+C] Exiting...")
    finally: system.shutdown()
