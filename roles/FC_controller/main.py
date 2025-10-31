from FuelCellController import FuelCellController
from alicat import Controller as AlicatController
import utils
import time
import sys
import select

SAVE_INTERVAL = 5  # seconds

def safe_float(val, default=0.0):
    """Return val as float if not None, else default."""
    try:
        return float(val) if val is not None else default
    except (ValueError, TypeError):
        return default

def print_user_options():
    print("\n--- USER COMMANDS ---")
    print("Press 'p' to set target power")
    print("Press 'o' to turn fuel cell ON")
    print("Press 'f' to turn fuel cell OFF")
    print("Press Ctrl+C to exit")
    print("----------------------\n")

def main():
    last_save_time = 0

    print("=== Fuel Cell Main ===")

    #step 0 alicat
    print("Initializing Alicat mass flow controller...")
    alicat = AlicatController()

    # Step 1: Bring up CAN bus
    print("Bringing up fuel cell CAN bus (can0)...")
    utils.canup_fuel_cell()
    time.sleep(1)

    # Step 2: Initialize fuel cell object
    fuel_cell = FuelCellController(debug=False)

    # Step 3: Set initial parameters
    print("Setting initial fuel cell parameters...")
    fuel_cell.set_voltage(54.0)   # Target 54 V
    fuel_cell.set_power(0.0)      # Start at 0 kW
    fuel_cell.fuelcell_on(False)  # Keep OFF on startup

    print("\n=== Fuel Cell Ready (OFF) ===\n")

    requested_power = 0.0
    fc_is_on = False

    # Step 4: Main loop
    try:
        while True:
            # Non-blocking keyboard input
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                key = sys.stdin.read(1).strip().lower()
                if key == 'p':
                    try:
                        target_power = float(input("Enter new target power (0 - 10 kW): "))
                        target_power = utils.clamp(0, target_power, 10)
                        requested_power = target_power
                        print(f"Setting target power to {target_power} kW...")
                        fuel_cell.set_power(target_power)
                        time.sleep(0.5)
                        if target_power > 0 and not fc_is_on:
                            fuel_cell.fuelcell_on(True)
                            fc_is_on = True
                    except ValueError:
                        print("Invalid input. Please enter a numeric value.")
                elif key == 'o':
                    print("Turning fuel cell ON...")
                    fuel_cell.fuelcell_on(True)
                    fc_is_on = True
                elif key == 'f':
                    print("Turning fuel cell OFF...")
                    fuel_cell.fuelcell_on(False)
                    fc_is_on = False

            # Read back values safely
            fc_power = safe_float(fuel_cell.get_fc_power())
            fc_voltage = safe_float(fuel_cell.get_system_output_voltage())
            fc_target_power = safe_float(fuel_cell.get_target_power())
            fc_target_voltage = safe_float(fuel_cell.get_target_voltage())
            fc_phase = fuel_cell.get_phase() or "N/A"
            fc_faults = fuel_cell.get_fault_codes() or []

            #alicat read
            #try except?
            try:
                alicat_data = alicat.poll()
                #print 
                mass_flow = alicat_data['M']
                volumetric_flow = alicat_data['V']
            except Exception as e:
                print(f"Error reading Alicat data: {e}")
                mass_flow = -1.0
                volumetric_flow = -1.0

            # Print system status
            print("=" * 40)
            print("FUEL CELL STATUS")
            #print time
            print(f"Time            : {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
            print(f"Phase           : {fc_phase}")
            print(f"System Voltage  : {fc_voltage:.2f} V")
            print(f"Target Voltage  : {fc_target_voltage:.2f} V")
            print(f"System Power    : {fc_power:.2f} kW")
            print(f"Target Power    : {fc_target_power:.2f} kW")
            print(f"Fuel Cell State : {'ON' if fc_is_on else 'OFF'}")
            print(f"Fault Codes     : {fc_faults}")
            print(f"Mass Flow       : {mass_flow:.2f} g/s")
            print(f"Volumetric Flow : {volumetric_flow:.2f} SLPM")
            print("=" * 40)

            # Print user options every loop
            print_user_options()

            #save mdot, vdot, power, voltage, current, to csv

            #fuel cell current
            fc_current = fc_power * 1000 / fc_voltage if fc_voltage > 0 else 0.0

            # only save if n seconds have passed
            if time.time() - last_save_time >= SAVE_INTERVAL:
                print("Saving data to vessel_1_5kW_run.csv...")
                utils.save_to_csv(
                    'vessel_1_5kW_run_2.csv',
                    [
                        time.time(),
                        mass_flow,
                        volumetric_flow,
                        fc_power,
                        fc_voltage,
                        fc_current
                    ],
                    header=["timestamp", "mass_flow_gps", "volumetric_flow_slpm", "fc_power_kw", "fc_voltage_v", "fc_current_a"]
                )
                last_save_time = time.time()
            

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down fuel cell safely...")
        fuel_cell.fuelcell_on(False)
        fuel_cell.system_on(False)
        fuel_cell.voltage_on(False)
        fuel_cell.close()
        print("Fuel cell shutdown complete.")

if __name__ == "__main__":
    main()
