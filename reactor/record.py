from .power import MP710256
import os
import time

# --------------------------
filename = 'reactor/outputs/test_log.csv'
override = True
voltage = 3.0
maximum_current = 1.0
interval = 1.0  # seconds
# --------------------------

if os.path.exists(filename) and not override:
    print(f"File '{filename}' already exists. Set 'override = True' to overwrite.")
else:
    with open(filename, 'w') as f:
        f.write('Time,Voltage (V),Current (A)\n')
        psu = MP710256(port = '/dev/ttyACM0', id = 1)
        psu.VSET = voltage
        psu.ISET = maximum_current
        psu.OUT = True  # Turn on the power supply
        start_time = time.time()
        try:
            while True:
                cycle_start = time.time()
                elapsed_time = cycle_start - start_time
                voltage_reading = psu.VOUT
                current_reading = psu.IOUT
                status = psu.STATUS
                print_status = {key: status[key] for key in ['CV MODE', 'OUTPUT']}
                print(f"----------\nTime: {elapsed_time:.3f}s\nVoltage: {voltage_reading:.3f}V\nCurrent: {current_reading:.3f}A\nStatus: {print_status}")
                f.write(f'{elapsed_time:.3f},{voltage_reading:.3f},{current_reading:.3f}\n')
                f.flush()  # Ensure data is written to file immediately
                while time.time() - cycle_start < interval:
                    # time.sleep(0.001)  # Small sleep to avoid tight loop
                    pass
        except KeyboardInterrupt:
            print("\n\nData logging stopped by user.")
        finally:
            psu.close()

