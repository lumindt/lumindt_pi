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

ENAPTER_HOSTS = [
    "10.1.10.53", "10.1.10.54", "10.1.10.55", "10.1.10.56",
    "10.1.10.57", "10.1.10.58", "10.1.10.59", "10.1.10.60"
]

DRYER_HOSTS = ["10.1.10.53", "10.1.10.57"]
DRYER_STATES = {
    257: 'WAITING FOR POWER', 263: 'WAITING FOR PRESSURE',
    259: 'STOPPED BY USER', 260: 'STARTING',
    262: 'STANDBY', 265: 'IDLE',
    513: 'DRYING', 514: 'COOLING', 515: 'SWITCHING',
    516: 'PRESSURIZING', 517: 'FINALIZING',
    1281: 'ERROR', 1537: 'BYPASS', 2305: 'MAINTENANCE'
}


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
    print("Press 'j' to START both dryers")
    print("Press 'k' to STOP both dryers")
    print("Press 'm' to switch mode")
    print("Press 'q' to exit")
    print("-------------------------------\n")


class L15System:
    def __init__(self):
        self.mode = "idle"
        self.controllers = {ip: ElectrolyzerModbusController(host=ip) for ip in ENAPTER_HOSTS}
        self.dryers = {ip: ElectrolyzerModbusController(host=ip) for ip in DRYER_HOSTS}

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
            self.start_dryers()  # Auto-start dryers in charge
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
            self.stop_dryers()

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
    def read_electrolyzer_data(self):
        """Read all electrolyzers’ data, including new production rate field."""
        data = {}
        total_flow = 0.0
        total_prod_rate = 0.0
        total_power = 0.0

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
            if not isnan(prod_rate):
                total_prod_rate += prod_rate
            if not isnan(power):
                total_power += power

            data[f"E{idx}_ip"] = ip
            data[f"E{idx}_state"] = state
            data[f"E{idx}_voltage"] = voltage
            data[f"E{idx}_current"] = current
            data[f"E{idx}_power_kW"] = power
            data[f"E{idx}_flow_NLh"] = flow
            data[f"E{idx}_prod_rate_NLh"] = prod_rate
            data[f"E{idx}_temp_C"] = temp

        data["total_flow_NLh"] = total_flow
        data["total_prod_rate_NLh"] = total_prod_rate
        data["total_power_kW"] = total_power
        return data

    # -------------------------------------------------------------------
    def read_dryer_states(self):
        rows = []
        for i, (ip, d) in enumerate(self.dryers.items(), start=1):
            try:
                code = safe_read(d.display_dryer_state, None)
                if code is None or (isinstance(code, float) and isnan(code)):
                    state = "Unavailable"
                else:
                    state = DRYER_STATES.get(int(code), f"Unknown ({code})")
            except Exception as e:
                state = f"Error: {e}"
            rows.append([i, ip, state])
        return rows

    def format_dryer_table(self, rows):
        return tabulate(rows, headers=["#", "IP", "Dryer State"], tablefmt="fancy_grid")

    def start_dryers(self):
        for d in self.dryers.values():
            try:
                d.write_start_dryer()
            except Exception as e:
                print(f"[DRYER] Start error: {e}")
        print("[DRYER] Start command sent to both dryers.")

    def stop_dryers(self):
        for d in self.dryers.values():
            try:
                d.write_stop_dryer()
            except Exception as e:
                print(f"[DRYER] Stop error: {e}")
        print("[DRYER] Stop command sent to both dryers.")

    # -------------------------------------------------------------------
    def read_fuelcell_block(self):
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
                    round(data.get(f"{prefix}prod_rate_NLh", 0), 1),
                    round(data.get(f"{prefix}temp_C", 0), 1),
                ])

        # Totals
        rows.append([
            "", "—", "TOTAL", "", "", round(data.get("total_power_kW", 0), 3),
            round(data.get("total_flow_NLh", 0), 1),
            round(data.get("total_prod_rate_NLh", 0), 1),
            ""
        ])

        headers = ["#", "IP", "State", "V (V)", "I (A)", "P (kW)",
                   "Flow (NL/h)", "Prod. Rate (%)", "Temp (°C)"]
        return tabulate(rows, headers=headers, tablefmt="fancy_grid")

    # -------------------------------------------------------------------
    def format_fuelcell_table(self, fc, al):
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

        while True:
            try:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                data = self.read_electrolyzer_data()
                fc = self.read_fuelcell_block()
                al = self.read_alicat_data()
                dryer_rows = self.read_dryer_states()

                print("\n" + "=" * 70)
                print(f"Timestamp: {now} | Mode: {self.mode.upper()}\n")
                print("ELECTROLYZER STATUS:")
                print(self.format_electrolyzer_table(data))
                print("\nFUEL CELL STATUS:")
                print(self.format_fuelcell_table(fc, al))
                print("\nDRYER STATUS:")
                print(self.format_dryer_table(dryer_rows))
                print("=" * 70)

                # Dynamic hotkey help
                if self.mode == "idle":
                    print("Hotkeys: 'm' switch mode | 'q' quit")

                elif self.mode == "charge":
                    print("Hotkeys: 'r' set production rate | 'm' switch mode | 'q' quit")

                elif self.mode == "discharge":
                    print("Hotkeys: 'p' set FC power | 'o' FC ON | 'f' FC OFF | 'm' switch mode | 'q' quit")


                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.read(1).strip().lower()
                    if key == "q":
                        print("Exiting system loop...")
                        break
                    elif key == "m":
                        print("\nSwitching mode...")
                        self.prompt_mode_change()
                        return
                    elif self.mode == "discharge" and self.fuelcell:
                        if key == "p":
                            try:
                                target = float(input("Enter target power (0–10 kW): ").strip())
                                if 0 <= target <= 10:
                                    self.fuelcell.set_power(target)
                                    print(f"[FC] Target power set to {target} kW.")
                                else:
                                    print("Invalid power value.")
                            except ValueError:
                                print("Invalid input.")
                        elif key == "o":
                            try:
                                self.fuelcell.fuelcell_on(True)
                                print("[FC] Fuel cell turned ON.")
                            except Exception as e:
                                print(f"[FC] ON error: {e}")
                        elif key == "f":
                            try:
                                self.fuelcell.fuelcell_on(False)
                                print("[FC] Fuel cell turned OFF.")
                            except Exception as e:
                                print(f"[FC] OFF error: {e}")
                    elif self.mode == "charge":
                        if key == "r":  # new hotkey to adjust electrolyzer production rate
                            try:
                                rate = float(input("Enter new target production rate (NL/h per stack): ").strip())
                                if rate < 0:
                                    print("Invalid rate.")
                                else:
                                    for ctrl in self.controllers.values():
                                        try:
                                            ctrl.write_target_production_rate(rate)
                                        except AttributeError:
                                            print(f"[WARN] Controller {ctrl} has no write_target_production_rate() method.")
                                        except Exception as e:
                                            print(f"[EL] Rate set error: {e}")
                                    print(f"[EL] Target production rate set to {rate} NL/h for all electrolyzers.")
                            except ValueError:
                                print("Invalid input.")

                                time.sleep(1)
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
        try:
            self.stop_dryers()
        except Exception:
            pass
        if self.fuelcell:
            try:
                self.fuelcell.close()
            except Exception:
                pass
        print("System safely stopped.")


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
