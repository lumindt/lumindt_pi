import sys
import select
import time
from datetime import datetime
from math import isnan
from enapter_modbus import ElectrolyzerModbusController

# =====================================================================================
ENAPTER_HOSTS = [ "10.1.10.53", "10.1.10.54", "10.1.10.55", "10.1.10.56", "10.1.10.57", "10.1.10.58", "10.1.10.59", "10.1.10.60" ]

# pick two controllers to represent the two dryers
DRYER_HOSTS = ["10.1.10.53", "10.1.10.57"]

DRYER_STATES = {
    257: 'WAITING FOR POWER', 263: 'WAITING FOR PRESSURE',
    259: 'STOPPED BY USER', 260: 'STARTING',
    262: 'STANDBY', 265: 'IDLE',
    513: 'DRYING', 514: 'COOLING', 515: 'SWITCHING',
    516: 'PRESSURIZING', 517: 'FINALIZING',
    1281: 'ERROR', 1537: 'BYPASS', 2305: 'MAINTENANCE'
}

# =====================================================================================
def safe_read(func, fallback=float("nan")):
    """Helper: safely call Modbus functions, return fallback if None or error."""
    try:
        val = func()
        if val is None:
            return fallback
        return val
    except Exception:
        return fallback

# =====================================================================================
def run_enapters():
    controllers = {ip: ElectrolyzerModbusController(host=ip) for ip in ENAPTER_HOSTS}
    dryers = {ip: ElectrolyzerModbusController(host=ip) for ip in DRYER_HOSTS}

    rate = float(input("Enter initial production rate (60–100%): "))
    for ctrl in controllers.values():
        ctrl.write_production_rate(rate)
        ctrl.write_stop_electrolyser()
    for d in dryers.values():
        d.write_stop_dryer()

    last_action = "System initialized (all OFF, dryers OFF)"

    initial_totals = {ip: safe_read(ctrl.display_stack_total_H2_production, 0.0) for ip, ctrl in controllers.items()}


    while True:
        curr_time = datetime.now()
        rows, total_flow, total_h2 = [], 0.0, 0.0

        for idx, (ip, ctrl) in enumerate(controllers.items(), start=1):
            try:
                stack_voltage = safe_read(ctrl.display_stack_voltage)
                stack_current = safe_read(ctrl.display_stack_current)
                stack_power = (stack_voltage * stack_current) / 1000 if not isnan(stack_voltage) and not isnan(stack_current) else float("nan")
                electrolyzer_on = safe_read(ctrl.display_start_stop_electrolyser, False)
                production_rate = safe_read(ctrl.display_production_rate)
                electrolyte_temp = safe_read(ctrl.display_electrolyte_temperature)
                stack_flow_rate = safe_read(ctrl.display_stack_H2_flow_rate)
                state = safe_read(ctrl.display_electrolyser_state, "Unknown")
                h2_total_now = safe_read(ctrl.display_stack_total_H2_production, 0.0)
                h2_total_session = h2_total_now - initial_totals.get(ip, 0.0)

                if not isnan(stack_flow_rate):
                    total_flow += stack_flow_rate
                if not isnan(h2_total_session):
                    total_h2 += h2_total_session

                rows.append([
                    f"E{idx}", ip, "ON" if electrolyzer_on else "OFF", state,
                    f"{production_rate:5.1f}%" if not isnan(production_rate) else "-",
                    f"{electrolyte_temp:5.1f}°C" if not isnan(electrolyte_temp) else "-",
                    f"{stack_voltage:6.1f}V" if not isnan(stack_voltage) else "-",
                    f"{stack_current:6.1f}A" if not isnan(stack_current) else "-",
                    f"{stack_power:6.2f}kW" if not isnan(stack_power) else "-",
                    f"{stack_flow_rate:6.1f}NL/h" if not isnan(stack_flow_rate) else "-",
                    f"{h2_total_session:.1f} NL"
                ])

            except Exception as e:
                rows.append([f"E{idx}", ip, "ERROR", "-", "-", "-", "-", "-", "-", "-", str(e)])


        dryer_statuses = []
        for i, (ip, d) in enumerate(dryers.items(), start=1):
            try:
                code = safe_read(d.display_dryer_state, None)
                state = "Unavailable" if code is None or isnan(code) else DRYER_STATES.get(code, f"Unknown ({code})")
                dryer_statuses.append(f"Dryer {i} ({ip}) State: {state}")
            except Exception as e:
                dryer_statuses.append(f"Dryer {i} ({ip}): Error {e}")

        print("\033c", end="")
        print(f"=== Enapter System Status @ {curr_time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        header = f"{'Unit':<6} {'IP':<14} {'Status':<6} {'State':<15} {'Rate':<7} {'Temp':<8} {'Voltage':<8} {'Current':<8} {'Power':<8} {'Flow':<10} {'H2 (NL)':<10}"
        print(header)
        print("-" * len(header))
        for row in rows:
            print(f"{row[0]:<6} {row[1]:<14} {row[2]:<6} {row[3]:<15} {row[4]:<7} {row[5]:<8} {row[6]:<8} {row[7]:<8} {row[8]:<8} {row[9]:<10} {row[10]:<10}")
        print("-" * len(header))

        print(f"TOTAL H2 Flow Rate: {total_flow:.1f} NL/h")
        print(f"TOTAL H2 Produced (since start): {total_h2:.1f} NL\n")
        for line in dryer_statuses:
            print(line)
        print("Controls: [s]=Start ALL, [x]=Stop ALL, [d]=Start Dryers, [f]=Stop Dryers, [r]=Change Prod Rate, [q]=Quit")
        print(f"Last Action: {last_action}")

        dr, _, _ = select.select([sys.stdin], [], [], 1)
        if dr:
            key = sys.stdin.read(1)
            if key == "s":
                print("Processing: Starting all electrolyzers...")
                for ctrl in controllers.values(): ctrl.write_start_electrolyser()
                last_action = "Started ALL electrolyzers"
            elif key == "x":
                print("Processing: Stopping all electrolyzers...")
                for ctrl in controllers.values(): ctrl.write_stop_electrolyser()
                last_action = "Stopped ALL electrolyzers"
            elif key == "d":
                print("Processing: Starting both dryers...")
                for d in dryers.values(): d.write_start_dryer()
                last_action = "Started BOTH dryers"
            elif key == "f":
                print("Processing: Stopping both dryers...")
                for d in dryers.values(): d.write_stop_dryer()
                last_action = "Stopped BOTH dryers"
            elif key == "r":
                try:
                    new_rate = float(input("Enter new production rate (60–100%): "))
                    for ctrl in controllers.values():
                        ctrl.write_production_rate(new_rate)
                    last_action = f"Changed production rate to {new_rate:.1f}%"
                except Exception as e:
                    last_action = f"Error changing rate: {e}"
            elif key == "q":
                print("Exiting...")
                return

# =====================================================================================
if __name__ == "__main__":
    run_enapters()
