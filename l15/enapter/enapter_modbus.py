from pyModbusTCP.client import ModbusClient
import pyModbusTCP.utils as ut
import time
from datetime import datetime
import csv

class ElectrolyzerModbusController:
    def __init__(self, host):
        self.IP = host
        self.electrolyzer = ModbusClient(host=host)

    def display_last_configuration_result(self):
        reg = self.electrolyzer.read_input_registers(4002, 1)
        if reg:
            state = reg[0]
            state_description = {
                0: "OK, Configuration was completed successfully",
                1: "Permanent, The operation has failed (internal or general error)",
                2: "No Entry, Configuration was not started or interrupted",
                5: "I/O, Data save error",
                11: "Try again, Configuration needs to be tried again",
                13: "Access Denied, Some changed registers are read-only",
                16: "Busy, Another configuration was in progress",
                22: "Invalid, The data has invalid or wrong type"
            }
            return state_description.get(state, "Unknown State")
        else:
            return "Failed to read last configuration result."

    def write_configuration_begin(self):
        self.electrolyzer.write_single_register(4000, 1)
        print("Configuration Begin set to 1")

    def write_configuration_commit(self, command):
        assert command in [0, 1], "Invalid command. Command must be 0 (rollback) or 1 (commit)."
        self.electrolyzer.write_single_register(4001, command)
        print("Configuration Commit set to", command)

    def display_configuration_progress(self):
        reg = self.electrolyzer.read_input_registers(4000, 1)
        if reg:
            return reg[0]
        else:
            return "Failed to read configuration progress."

    def write_max_tank_pressure(self, value):
        if self.display_configuration_progress() != 0:
            print("Configuration is in progress. Rolling back to 0.")
            self.write_configuration_commit(0)  # rollback

        self.write_configuration_begin()
        time.sleep(1)

        encoded_value = ut.encode_ieee(value)
        value_to_write = ut.long_list_to_word([encoded_value])
        self.electrolyzer.write_multiple_registers(4308, value_to_write)

        self.write_configuration_commit(1)

        result = self.display_last_configuration_result()
        if result != "OK, Configuration was completed successfully":
            print("Configuration failed.")
        else:
            print("Configuration successful.")

    def write_restart_pressure(self, value):
        if self.display_configuration_progress() != 0:
            print("Configuration is in progress. Rolling back to 0.")
            self.write_configuration_commit(0)  # rollback

        self.write_configuration_begin()
        time.sleep(1)

        encoded_value = ut.encode_ieee(value)
        value_to_write = ut.long_list_to_word([encoded_value])
        self.electrolyzer.write_multiple_registers(4310, value_to_write)

        self.write_configuration_commit(1)

        result = self.display_last_configuration_result()
        if result != "OK, Configuration was completed successfully":
            print("Configuration failed.")
        else:
            print("Configuration successful.")

    def write_default_production_rate(self, value):
        state = self.display_electrolyser_state()
        if state not in ['Idle', 'Maintenance Mode']:
            print(f"Cannot set Default Production Rate. Electrolyser is in {state} state.")
            return

        if self.display_configuration_progress() != 0:
            print("Configuration is in progress. Rolling back to 0.")
            self.write_configuration_commit(0)  # rollback

        self.write_configuration_begin()
        time.sleep(1)

        encoded_value = ut.encode_ieee(value)
        value_to_write = ut.long_list_to_word([encoded_value])
        self.electrolyzer.write_multiple_registers(4396, value_to_write)

        self.write_configuration_commit(1)

        result = self.display_last_configuration_result()
        if result != "OK, Configuration was completed successfully":
            print("Failed to set Default Production Rate.")
        else:
            print(f"Default Production Rate set to {value} %")

    def display_system_state(self):
        reg = self.electrolyzer.read_input_registers(18, 1)
        if reg:
            state = reg[0]
            state_description = {
                0: "Internal Error, System not Initialized yet",
                1: "System in Operation",
                2: "Error",
                3: "System in Maintenance Mode",
                4: "Fatal Error",
                5: "System in Expert Mode"
            }
            return state_description.get(state, "Unknown State")
        else:
            return "Failed to read system state."

    def display_stack_total_H2_production(self):
        reg = self.electrolyzer.read_input_registers(1006, 2)
        return ut.decode_ieee(ut.word_list_to_long(reg)[0])

    def display_stack_H2_flow_rate(self):
        reg = self.electrolyzer.read_input_registers(1008, 2)
        return ut.decode_ieee(ut.word_list_to_long(reg)[0])

    def display_electrolyser_state(self):
        reg = self.electrolyzer.read_input_registers(1200, 1)
        if reg:
            state = reg[0]
            state_description = {
                0: "Halted",
                1: "Maintenance Mode",
                2: "Idle",
                3: "Steady",
                4: "Stand-By (Max Pressure)",
                5: "Curve"
            }
            return state_description.get(state, "Unknown State")
        else:
            return "Failed to read electrolyser state."

    def display_dryer_PT01_min_threshold(self):
        reg = self.electrolyzer.read_input_registers(6014, 2)
        return ut.decode_ieee(ut.word_list_to_long(reg)[0])
    
    def display_dryer_PT01_max_threshold(self):
        reg = self.electrolyzer.read_input_registers(6016, 2)
        return ut.decode_ieee(ut.word_list_to_long(reg)[0])

    def display_dryer_state(self):
        reg = self.electrolyzer.read_input_registers(6021, 1)
        return reg[0]
    
    '''
    6018	Boolean	Start/Stop Dryer	Write: 1 = Start; 0 = Stop. Read register #6021 to check Dryer Logic States. Avoid frequent write operations, since it can damage Dryer's Flash.'''

    def write_start_dryer(self):
        self.electrolyzer.write_single_register(6018, 1)
    
    def write_stop_dryer(self):
        self.electrolyzer.write_single_register(6018, 0)

    

    def display_stack_current(self):
        reg = self.electrolyzer.read_input_registers(7508, 2)
        return ut.decode_ieee(ut.word_list_to_long(reg)[0])

    def display_stack_voltage(self):
        reg = self.electrolyzer.read_input_registers(7510, 2)
        return ut.decode_ieee(ut.word_list_to_long(reg)[0])

    def display_electrolyte_temperature(self):
        reg = self.electrolyzer.read_input_registers(7518, 2)
        return ut.decode_ieee(ut.word_list_to_long(reg)[0])

    def display_gas_presence(self):
        reg = self.electrolyzer.read_input_registers(7538, 2)
        return ut.decode_ieee(ut.word_list_to_long(reg)[0])

    def display_warning_codes(self):
        reg = self.electrolyzer.read_input_registers(768, 1)
        if reg:
            num_warnings = reg[0]
            warning_codes = []
            for i in range(num_warnings):
                reg = self.electrolyzer.read_input_registers(769 + i, 1)
                if reg:
                    warning_codes.append(reg[0])
            return warning_codes
        else:
            return "Failed to read warning codes."

    def display_error_codes(self):
        reg = self.electrolyzer.read_input_registers(832, 1)
        if reg:
            num_errors = reg[0]
            error_codes = []
            for i in range(num_errors):
                reg = self.electrolyzer.read_input_registers(833 + i, 1)
                if reg:
                    error_codes.append(reg[0])
            return error_codes
        else:
            return "Failed to read error codes."

    def display_start_stop_electrolyser(self):
        reg = self.electrolyzer.read_holding_registers(1000, 1)
        if reg:
            return bool(reg[0])
        else:
            return "Failed to read start/stop electrolyser."

    def display_production_rate(self):
        reg = self.electrolyzer.read_holding_registers(1002, 2)
        return ut.decode_ieee(ut.word_list_to_long(reg)[0])

    def display_force_water_refilling(self):
        reg = self.electrolyzer.read_holding_registers(1011, 1)
        if reg:
            return bool(reg[0])
        else:
            return "Failed to read force water refilling."

    def display_maintenance_mode(self):
        reg = self.electrolyzer.read_holding_registers(1013, 1)
        if reg:
            return bool(reg[0])
        else:
            return "Failed to read maintenance mode."

    def display_preheat(self):
        reg = self.electrolyzer.read_holding_registers(1014, 1)
        if reg:
            return bool(reg[0])
        else:
            return "Failed to read preheat."

    def write_start_electrolyser(self):
        self.electrolyzer.write_single_register(1000, 1)

    def write_stop_electrolyser(self):
        self.electrolyzer.write_single_register(1000, 0)

    def write_production_rate(self, value):
        value = max(60, min(100, value))
        encoded_value = ut.encode_ieee(value)
        value_to_write = ut.long_list_to_word([encoded_value])
        self.electrolyzer.write_multiple_registers(1002, value_to_write)

    def write_preheat(self, value):
        assert value in [0, 1], "Invalid value. Value must be 0 or 1."
        self.electrolyzer.write_single_register(1014, value)

    def read_preheat(self):
        reg = self.electrolyzer.read_holding_registers(1014, 1)
        return reg[0]
    
    '''6010	Float32	Dryer PT00	Input pressure of the dryer.'''
    def display_dryer_PT00(self):
        reg = self.electrolyzer.read_input_registers(6010, 2)
        return ut.decode_ieee(ut.word_list_to_long(reg)[0])

    '''6012	Float32	Dryer PT01	Output pressure of the dryer.'''
    def display_dryer_PT01(self):
        reg = self.electrolyzer.read_input_registers(6012, 2)
        return ut.decode_ieee(ut.word_list_to_long(reg)[0])
    
    '''1008	Float32	H2 Flow Rate	NL/hour, NAN when not producing H2;'''
    def display_stack_H2_flow_rate(self):
        reg = self.electrolyzer.read_input_registers(1008, 2)
        return ut.decode_ieee(ut.word_list_to_long(reg)[0])
    
    '''6014	Float32	PT01 minimal threshold	Dryer output pressure at which it leaves Stand-by. Updated value is saved only after writing 1 to register #6022.'''
    def write_dryer_PT01_min_threshold(self, value):
        encoded_value = ut.encode_ieee(value)
        value_to_write = ut.long_list_to_word([encoded_value])
        self.electrolyzer.write_multiple_registers(6014, value_to_write)
    
    '''6016	Float32	PT01 maximal threshold	Dryer output pressure at which it moves to Stand-by. Updated value is saved only after writing 1 to register #6022.'''
    def write_dryer_PT01_max_threshold(self, value):
        encoded_value = ut.encode_ieee(value)
        value_to_write = ut.long_list_to_word([encoded_value])
        self.electrolyzer.write_multiple_registers(6016, value_to_write)
    
    '''6022	Uint16	Save updated Dryer configuration	Write: 1 = Save updated Dryer configuration on flash. Avoid frequent write operations, since it can damage Dryer's Flash.'''
    def write_save_dryer_configuration(self):
        self.electrolyzer.write_single_register(6022, 1)

#================================================================================================ 

if __name__ == "__main__":
    elec = ElectrolyzerModbusController(host='10.1.10.231')
    actuate = False

    #stop the electrolyzer
    if actuate: elec.write_stop_electrolyser()

    production_rate = input("Enter the production rate between 60 and 100%: ")
    elec.write_production_rate(float(production_rate))

    with open('electrolyzer_data.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            "Time", 
            "Electrolyzer Status", 
            "Preheat Status", 
            "Production Rate (%)", 
            "Electrolyte Temperature (°C)", 
            "Stack Voltage (V)", 
            "Stack Current (A)", 
            "Stack Power (kW)",
            "Stack H2 Flow Rate (NL/hour)"
        ])

        i = 0
        while True:
            if i == 10:
                if actuate: elec.write_start_electrolyser()
                pass

            curr_time = datetime.now()
            stack_voltage = elec.display_stack_voltage()
            stack_current = elec.display_stack_current()
            stack_power = (stack_voltage * stack_current) / 1000  # Convert to kW
            electrolyzer_ison = elec.display_start_stop_electrolyser()
            production_rate = elec.display_production_rate()
            preheat_status = elec.display_preheat()
            electrolyte_temp = elec.display_electrolyte_temperature()
            stack_flow_rate = elec.display_stack_H2_flow_rate()
            dryer_state = elec.display_dryer_state()


            print("=" * 30)
            print(f"Current Time: {curr_time}")
            print(f"Electrolyzer Status: {'ON' if electrolyzer_ison else 'OFF'}")
            print(f"Preheat Status: {'ON' if preheat_status else 'OFF'}")
            print(f"Production Rate: {production_rate}%")
            print(f"Electrolyte Temperature: {electrolyte_temp} °C")
            print(f"Stack Voltage: {stack_voltage} V")
            print(f"Stack Current: {stack_current} A")
            print(f"Stack Power: {stack_power} kW")
            print(f"Stack H2 Flow Rate: {stack_flow_rate} NL/hour")
            print(f"Dryer State: {dryer_state}")
            print("=" * 30)

            # writer.writerow([
            #     curr_time.strftime('%Y-%m-%d %H:%M:%S'), 
            #     "ON" if electrolyzer_ison else "OFF", 
            #     "ON" if preheat_status else "OFF", 
            #     production_rate, 
            #     electrolyte_temp, 
            #     stack_voltage, 
            #     stack_current, 
            #     stack_power,
            #     stack_flow_rate
            # ])

            # file.flush()
            # i += 1
            # time.sleep(1)  # Add a delay to avoid spamming the log file