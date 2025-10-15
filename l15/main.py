import time
import sys
import select
from datetime import datetime
from math import isnan
from tabulate import tabulate
from enapter.enapter_modbus import ElectrolyzerModbusController
from horizon_fc.FuelCellController import FuelCellController
from horizon_fc.alicat import Controller as AlicatController
import utils

SAVE_INTERVAL = 5  # seconds
ENAPTER_HOSTS = [
    "10.1.10.53", "10.1.10.54", "10.1.10.55", "10.1.10.56",
    "10.1.10.57", "10.1.10.58", "10.1.10.59", "10.1.10.60"
]


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


def print_fc_user_options():
    print("\n--- USER COMMANDS (DISCHARGE) ---")
    print("Press 'p' to set target power (0–10 kW)")
    print("Press 'o' to turn fuel cell ON")
    print("Press 'f' to turn fuel cell OFF")
    print("Press 'm' to switch mode")
    print("Press 'q' to exit")
    print("-------------------------------\n")


class L15System:
    def __init__(self):
        self.mode = "idle"
        self.last_save = 0
        self.controllers = {ip: ElectrolyzerModbusController(host=ip) for ip in ENAPTER_HOSTS}

        # Alicat init
        try:
            print("Initializing Alicat controller...")
            self.alicat = AlicatController()
            self.alicat_ready = True
        except Exception as e:
            print(f"[WARN] Alicat init failed: {e}")
            self.alicat_ready = False
            self.alicat = None

        # Fuel cell init — handle missing CAN gracefully
        try:
            print("Initializing FuelCellController...")
            self.fuelcell = FuelCellController(debug=False)
            if not getattr(self.fuelcell, "online", True):
                print("[WARN] Fuel cell offline (no CAN detected). Continuing in offline mode.")
        except Exception as e:
            print(f"[WARN] FuelCellController init failed: {e}")
            self.fuelcell = None

    # -------------------------------------------------------------------
    def set_mode(self, mode):
        mode = mode.lower()
        if mode not in ["charge", "discharge", "idle"]:
            print("Invalid mode.")
            return
        self.mode = mode
        print(f"\n=== MODE: {mode.upper()} ===")

        if mode == "charge":
            self.start_electrolyzers()
            self.stop_fuelcell()

        elif mode == "discharge":
            self.stop_electrolyzers()
            if self.fuelcell:
                try:
                    self.fuelcell.set_voltage(54.0)
                    self.fuelcell.set_power(0.0)
                    self.fuelcell.fuelcell_on(False)
                    print("[FC] Armed (OFF): target 54 V, 0 kW.")
                except Exception as e:
                    print(f"[FC] Arm error: {e}")

        else:
            self.stop_electrolyzers()
            self.stop_fuelcell()

    # -------------------------------------------------------------------
    def start_electrolyzers(self):
        for ctrl in self.controllers.values():
            ctrl.write_start_electrolyser()
        print("[EL] Electrolyzers started.")

    def stop_electrolyzers(self):
        for ctrl in self.controllers.values():
            ctrl.write_stop_electrolyser()
        print("[EL] Electrolyzers stopped.")

    def stop_fuelcell(self):
        if self.fuelcell:
            try:
                self.fuelcell.fuelcell_on(False)
                self.fuelcell.system_on(False)
                self.fuelcell.voltage_on(False)
                print("[FC] Fuel cell stopped.")
            except Exception as e:
                print(f"[FC] Stop error: {e}")

    # -------------------------------------------------------------------
    # ---------- CHARGE: Enapter Read ----------
    def read_electrolyzer_data(self):
        data = {}
        total_flow = 0.0
        for idx, (ip, ctrl) in enumerate(self.controllers.items(), start=1):
            voltage = safe_read(ctrl.display_stack_voltage)
            current = safe_read(ctrl.display_stack_current)
            power = (voltage * current) / 1000 if not isnan(voltage) and not isnan(current) else float("nan")
            flow = safe_read(ctrl.display_stack_H2_flow_rate)
            temp = safe_read(ctrl.display_electrolyte_temperature)
            state = safe_read(ctrl.display_electrolyser_state, "Unknown")
            if not isnan(flow):
                total_flow += flow

            data[f"E{idx}_ip"] = ip
            data[f"E{idx}_state"] = state
            data[f"E{idx}_voltage"] = voltage
            data[f"E{idx}_current"] = current
            data[f"E{idx}_power_kW"] = power
            data[f"E{idx}_flow_NLh"] = flow
            data[f"E{idx}_temp_C"] = temp

        data["total_flow_NLh"] = total_flow
        return data

    # ---------- DISCHARGE: Fuel Cell + Alicat ----------
    def read_fuelcell_block(self):
        """Return a dict with FC values needed for the status block."""
        if not self.fuelcell:
            return dict(
                fc_power_kW=0.0,
                fc_voltage_V=0.0,
                fc_target_power_kW=0.0,
                fc_target_voltage_V=0.0,
                fc_phase="N/A",
                fc_faults=[]
            )

        fc_power = safe_float(self.fuelcell.get_fc_power())
        fc_voltage = safe_float(self.fuelcell.get_system_output_voltage())
        fc_target_power = safe_float(self.fuelcell.get_target_power())
        fc_target_voltage = safe_float(self.fuelcell.get_target_voltage())
        fc_phase = self.fuelcell.get_phase() or "N/A"
        fc_faults = self.fuelcell.get_fault_codes() or []

        return dict(
            fc_power_kW=fc_power,
            fc_voltage_V=fc_voltage,
            fc_target_power_kW=fc_target_power,
            fc_target_voltage_V=fc_target_voltage,
            fc_phase=fc_phase,
            fc_faults=fc_faults
        )

    def read_alicat_data(self):
        if not self.alicat_ready or not self.alicat:
            return {"mass_flow_gps": -1.0, "volumetric_flow_slpm": -1.0}
        try:
            data = self.alicat.poll()
            return {"mass_flow_gps": data.get("M", -1.0), "volumetric_flow_slpm": data.get("V", -1.0)}
        except Exception as e:
            print(f"[WARN] Alicat read failed: {e}")
            return {"mass_flow_gps": -1.0, "volumetric_flow_slpm": -1.0}

    # -------------------------------------------------------------------
    def format_electrolyzer_table(self, data):
        """Create a table for all electrolyzers."""
        rows = []
        for i in range(1, 9):
            prefix = f"E{i}_"
            if f"{prefix}ip" in data:
                rows.append([
                    i,
                    data.get(f"{prefix}ip", ""),
                    data.get(f"{prefix}state", ""),
                    round(data.get(f"{prefix}voltage", 0), 3),
                    round(data.get(f"{prefix}current", 0), 3),
                    round(data.get(f"{prefix}power_kW", 0), 5),
                    round(data.get(f"{prefix}flow_NLh", 0), 1),
                    round(data.get(f"{prefix}temp_C", 0), 1),
                ])
        headers = ["#", "IP", "State", "V (V)", "I (A)", "P (kW)", "Flow (NL/h)", "Temp (°C)"]
        return tabulate(rows, headers=headers, tablefmt="fancy_grid")

    def format_fuelcell_table(self, fc, al):
        """Create a small summary table for the fuel cell."""
        rows = [[
            fc.get("fc_phase", "N/A"),
            round(fc.get("fc_voltage_V", 0), 2),
            round(fc.get("fc_power_kW", 0), 2),
            round(fc.get("fc_target_voltage_V", 0), 2),
            round(fc.get("fc_target_power_kW", 0), 2),
            round(al.get("mass_flow_gps", 0), 2),
            round(al.get("volumetric_flow_slpm", 0), 2),
        ]]
        headers = [
            "Phase", "Voltage (V)", "Power (kW)", "Target V", "Target P",
            "Mass Flow (g/s)", "Vol Flow (SLPM)"
        ]
        return tabulate(rows, headers=headers, tablefmt="fancy_grid")

    # -------------------------------------------------------------------
    def run_loop(self):
        print(f"Running system in {self.mode.upper()} mode. (Press Ctrl+C to exit)")

        if self.mode == "discharge":
            last_save_time = 0
            fc_is_on = False

            while True:
                try:
                    now_str = time.strftime('%Y-%m-%d %H:%M:%S')

                    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                        key = sys.stdin.read(1).strip().lower()
                        if key == 'p' and self.fuelcell:
                            try:
                                target_power = float(input("Enter new target power (0 - 10 kW): "))
                                target_power = utils.clamp(0, target_power, 10)
                                print(f"Setting target power to {target_power} kW...")
                                self.fuelcell.set_power(target_power)
                                time.sleep(0.3)
                                if target_power > 0:
                                    self.fuelcell.fuelcell_on(True)
                                    fc_is_on = True
                            except ValueError:
                                print("Invalid input.")
                        elif key == 'o' and self.fuelcell:
                            self.fuelcell.fuelcell_on(True)
                            fc_is_on = True
                        elif key == 'f' and self.fuelcell:
                            self.fuelcell.fuelcell_on(False)
                            fc_is_on = False
                        elif key == 'm':
                            print("\nSwitching mode...")
                            self.prompt_mode_change()
                            return
                        elif key == 'q':
                            print("Exiting discharge loop...")
                            break

                    fc = self.read_fuelcell_block()
                    al = self.read_alicat_data()
                    ec_data = self.read_electrolyzer_data()

                    print("\n" + "=" * 70)
                    print(f"Timestamp: {now_str} | Mode: {self.mode.upper()}\n")
                    print("FUEL CELL STATUS:")
                    print(self.format_fuelcell_table(fc, al))
                    print("\nELECTROLYZER STATUS:")
                    print(self.format_electrolyzer_table(ec_data))
                    print("=" * 70)
                    print_fc_user_options()

                    time.sleep(1)

                except KeyboardInterrupt:
                    break
            return

        # CHARGE / IDLE
        while True:
            try:
                start = time.time()
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                data = self.read_electrolyzer_data()
                fc = self.read_fuelcell_block()
                al = self.read_alicat_data()

                print("\n" + "=" * 70)
                print(f"Timestamp: {now} | Mode: {self.mode.upper()}\n")
                print("ELECTROLYZER STATUS:")
                print(self.format_electrolyzer_table(data))
                print("\nFUEL CELL STATUS:")
                print(self.format_fuelcell_table(fc, al))
                print("=" * 70)

                if time.time() - self.last_save >= SAVE_INTERVAL:
                    utils.save_to_csv(
                        f"system_{self.mode}_log.csv",
                        [now] + list(data.values()),
                        header=["timestamp"] + list(data.keys())
                    )
                    self.last_save = time.time()

                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.read(1).strip().lower()
                    if key == "q":
                        print("Exiting system loop...")
                        break
                    elif key == "m":
                        print("\nSwitching mode...")
                        self.prompt_mode_change()
                        return

                time.sleep(max(0, 1 - (time.time() - start)))
            except KeyboardInterrupt:
                break

    # -------------------------------------------------------------------
    def prompt_mode_change(self):
        print("\n--- MODE SWITCH ---")
        print("1. Charge (Electrolyzers ON)")
        print("2. Discharge (Fuel Cell ON - user controls)")
        print("3. Idle (All OFF)")
        choice = input("Select new mode [1–3]: ").strip()
        new_mode = "charge" if choice == "1" else "discharge" if choice == "2" else "idle"
        self.set_mode(new_mode)
        self.run_loop()

    # -------------------------------------------------------------------
    def shutdown(self):
        print("\nSystem shutdown...")
        self.stop_electrolyzers()
        self.stop_fuelcell()
        if self.fuelcell:
            try:
                self.fuelcell.close()
            except Exception:
                pass
        print("System safely stopped.")


# ==============================================================
if __name__ == "__main__":
    system = L15System()
    try:
        print("Select mode:")
        print("1. Charge (Electrolyzers ON)")
        print("2. Discharge (Fuel Cell ON - user controls)")
        print("3. Idle (All OFF)")
        choice = input("Enter choice [1–3]: ").strip()
        system.set_mode("charge" if choice == "1" else "discharge" if choice == "2" else "idle")
        system.run_loop()
    except KeyboardInterrupt:
        pass
    finally:
        system.shutdown()
