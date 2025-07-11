import serial
import time

class Controller:
    def __init__(self, port='/dev/ttyUSB0', baudrate=19200, address='A', timeout=0.5, **units):
        self.address = address.upper()
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout
            )
        except serial.SerialException as e:
            raise RuntimeError(f'Failed to open serial port: {e}')
        
        self._send_command('TC 1 -1 0 -1 7 0') # Sets up Totalizer 1
        self._send_command('TC 2 1') # Polling relies on knowing only one totalizer is active, dissables totalizer 2
        self._send_command('GS 6') # Set default gas to H2 (number 6)
        self.cancel_hold()  # Ensure no hold command is active
        
        self.gas_dict = {
            'H2': { 'number': 6, 'SCCM2G': 8.988e-5},
            'O2': { 'number': 11, 'SCCM2G': 1.429e-4},
            'N2': { 'number': 8, 'SCCM2G': 1.250e-4},
        }

        self.unit_label_dict = {
            "Mass flow": 5,
            "Volumetric flow": 4,
            "Pressure": 2,
            "Total mass": 9,
            "Mass flow setpoint": 37,
            "Temperature": 3, 
        }
        self.unit_value_dict = {
            "Mass flow": {
                "mg/s":   64,   # Milligram per second
                "mg/m":   65,   # Milligram per minute
                "g/s":    66,   # Gram per second
                "g/m":    67,   # Gram per minute
                "g/h":    68,   # Gram per hour
                "kg/m":   69,   # Kilogram per minute
                "kg/h":   70,   # Kilogram per hour
            },
            "Volumetric flow": {
                "µL/min":  2,   # Standard microliter per minute
                "mL/min":  3,   # Standard milliliter per minute
                "mL/s":    4,   # Standard milliliter per second
                "mL/h":    5,   # Standard milliliter per hour
                "L/min":   6,   # Standard liter per minute
                "L/s":     7,   # Standard liter per second
                "L/h":     8,   # Standard liter per hour
            },
            "Pressure": {
                "Pa":      2,   # Pascal
                "kPa":     4,   # Kilopascal
                "MPa":     5,   # Megapascal
                "mbar":    6,   # Millibar
                "bar":     7,   # Bar
                "g/cm²":  8,   # Gram-force per square centimeter
                "kg/cm²":  9,   # Kilogram-force per square centimeter
                "PSI":    10,   # Pound-force per square inch
            },
            "Temperature":{
                "C": 2,    # Degree Celsius
                "F": 3,    # Degree Fahrenheit
                "K": 4,     # Kelvin
            },
            "Mass flow setpoint": {
                "mg/s":   64,   # Milligram per second
                "mg/m":   65,   # Milligram per minute
                "g/s":    66,   # Gram per second
                "g/m":    67,   # Gram per minute
                "g/h":    68,   # Gram per hour
                "kg/m":   69,   # Kilogram per minute
                "kg/h":   70,   # Kilogram per hour
            }
        }

        self.status_dict = {
            "TMF": "Totalizer missed mass flow data. Possibly due to high mass flow rate or high volumetric flow rate.",
            "HLD": "Hold command active. The valve is held in current position. NO ERROR",
            "EXH": "Exhaust valve is open. NO ERROR",
            "MOV": "Mass flow rate overage.",
            "VOV": "Volumetric flow rate overage.",
            "OVR": "Totalizer has rolled over or is frozen at max value."
        }

        self.totalizer_reset(1)
        
        UNIT_DEFAULTS = {
            "mass_flow":          "g/s",
            "volumetric_flow":    "L/min",
            "pressure":           "bar",
            "temperature":        "C",
            "mass_setpoint":      "g/s",
        }

        requested_units = UNIT_DEFAULTS.copy()
        requested_units |= units

        # set units based on paramaters of init
        self._set_units("Mass flow", requested_units["mass_flow"])  # Set default mass flow units
        self._set_units("Volumetric flow", requested_units["volumetric_flow"])  # Set default volumetric flow units
        self._set_units("Pressure", requested_units["pressure"])  # Set default pressure units
        self._set_units("Temperature", requested_units["temperature"])  # Set default temperature units
        self._set_units("Mass flow setpoint", requested_units["mass_setpoint"])  # Set default mass flow setpoint units

        self.chosen_units = self.units

        CLEAN = str.maketrans('', '', '`') 
        self.chosen_units['Temperature']['unit_label'] = self.chosen_units['Temperature']['unit_label'].translate(CLEAN)  # Remove backticks from temperature unit label

        total_mass_unit = self.units['Total mass']['unit_numerical_value']  # Get the unit numerical value for total mass
        self._validate_total_mass_unit(total_mass_unit)

        self.mass_flow_totals = []

    ### UTILITIES ###
    def _send_command(self, command):
        full_command = f'{self.address}{command}\r'.encode('utf-8')
        self.ser.write(full_command)
        time.sleep(0.1)
        resp=self.ser.read_until(b'\r').decode('utf-8').strip().split()
        return resp


    def _validate_total_mass_unit(self, total_mass_unit):
        if total_mass_unit != 6:
            raise ValueError(
                f"Total mass unit {total_mass_unit} requires a conversion "
                f"factor, note that the default is set for SCCM."
            )

    def _set_units(self, label, value):
        unit_type = label
        if value not in self.unit_value_dict[unit_type]:
            raise ValueError(f'Invalid unit value: {value}. Available values: {list(self.unit_value_dict[unit_type].keys())}')
        
        label_nummarized = self.unit_label_dict[label]
        value_nummarized = self.unit_value_dict[unit_type][value]
        resp = self._send_command(f'DCU {label_nummarized} {value_nummarized}')
        return {
            "unit_numerical_value": int(resp[1]),
            "unit_label": resp[2]
        } 


    ### POLLING ###

    def poll(self):
        '''Poll flow, pressure, and temperature.'''
        data=self._send_command('')
        units=self.chosen_units
        
        data_dict = {
            'U': data[0],
            'P': (float(data[1]), units['Pressure']['unit_label']),  # Downstream pressure
            'T': (float(data[2]), units['Temperature']['unit_label']),  # Gas temperature
            'V': (float(data[3]), units['Volumetric flow']['unit_label']),  # Volumetric flow
            'M': (float(data[4]), units['Mass flow']['unit_label']),  # Mass flow
            'S': (float(data[5]), units['Mass flow setpoint']['unit_label']),  # Mass flow setpoint
            'A': ((float(data[6]) * list(self.gas_dict.get(self.gas['formula']).values())[1]) + (self.mass_flow_totals[-1] if self.mass_flow_totals else 0), 'g'),  # Accumulated mass (g)
            'G': data[7],
            'E': []
        }
        for code in data[8:]:
            data_dict['E'].append(code)
            if code == "TMF":
                try:
                    self.mass_flow_totals.append(data_dict['A'][0])
                    self.totalizer_reset(1, manual_reset=False)  # Reset totalizer if mass flow data is missed
                except Exception as e:
                    print(f"Error resetting totalizer: {e}")
            elif code in self.status_dict:
                print(self.status_dict.get(code, f'Unknown status code: {code}'))
        
        return data_dict

    ### CONTROL ###
    @property
    def setpoint(self):
        resp=self._send_command('LS')
        return float(resp[1])

    @setpoint.setter
    def setpoint(self,value):
        self._send_command(f'LS {value}')

    ### RAMP RATE ###
    @property
    def ramp(self):
        resp=self._send_command('SR')
        return float(resp[1])

    @ramp.setter
    def ramp(self,new_ramp):
        self._send_command(f'SR {new_ramp} 4') # rate is tied to units of mass flow rate units; set to zero to disable

    def hold_closed(self):
        '''Hold the valve closed.'''
        resp = self._send_command('HC')
        if "HLD" not in resp:
            raise RuntimeError(f'Failed to hold closed: {resp}')
    
   # TODO: THIS currently does not work. There is no function to easily fully open. The controller will need to be commanded to the max setpoint, but this needs to be made extendable for different units
    # def hold_open(self):
    #     print(self._send_command('S 100')) 
      
    #     resp = self._send_command('HP')
    #     if "HLD" not in resp:
    #         raise RuntimeError(f'Failed to hold open: {resp}')
    
    def cancel_hold(self):
        '''Cancel the hold closed command.'''
        resp = self._send_command('C')
        if "HLD"  in resp:
            raise RuntimeError(f'Failed to cancel hold: {resp}')

    ### GAS ### 
    
    @property
    def gas(self):
        resp=self._send_command(f'GS')
        return {'number':int(resp[1]),'formula':resp[2],'name':resp[3]}
    
    @gas.setter
    def gas(self,formula):
        if formula.isdigit():
            number=int(formula)
        elif formula in self.gas_dict:
            number=self.gas_dict[formula]['number']
        else:
            raise ValueError(f'Invalid gas formula: {formula}. Available gases: {list(self.gas_dict.keys())}')
        self._send_command(f'G {number}')

    ### TOTALIZER ###

    def totalizer_reset(self,num, manual_reset=True):
        '''Reset totalizer either num 1 or 2'''
        if num not in [1, 2]:
            raise ValueError('Totalizer number must be 1 or 2.')
        if manual_reset:
            self.mass_flow_totals = []
        print(self._send_command(f'T {num}'))

    def totalizer_config(self, num, statistic, mode):
        """
        Configure totalizer settings.

        Args:
            num (int): Totalizer number (1 or 2).
            statistic (str): Statistic to configure ('flow', 'pressure').
            mode (str): Mode of operation (pos, neg, net).

        Returns:
            Response from the device.
        """
        if num not in [1, 2]:
            raise ValueError('Totalizer number must be 1 or 2.')
        if statistic not in ['flow', 'pressure']:
            raise ValueError('Statistic must be one of: flow, pressure.')
        if mode not in ['pos', 'neg', 'net']:
            raise ValueError('Mode must be one of: pos, negative, net.')

        # Map statistic and mode to the command format
        if statistic == 'flow':
            statistic = 5
        elif statistic == 'pressure':
            statistic = 2
        if mode == 'pos':
            mode = 0
        elif mode == 'neg':
            mode = 1
        elif mode == 'net':
            mode = 2

        cmd = f'TC {num} {statistic} {mode} -1 7 0'
        self._send_command(cmd)
        # send command to other totalizer to disable it
        self._send_command(f'TC {3-num} 1')  # Disable the other totalizer
        return f'Totalizer {num} configured with statistic {statistic} and mode {mode}.'

    ### UNITS ###
    @property
    def units(self):
        """
        Get the current engineering units for all available labels.

        Returns:
            A dictionary mapping each label to its current unit value and label.
        """
        units = {}

        for label, label_nummarized in self.unit_label_dict.items():
            resp = self._send_command(f'DCU {label_nummarized}')
             # add unit_numerical_value and unit_label to the dictionary
            if len(resp) < 3:
                raise ValueError(f'Invalid response for label {label}: {resp}')
            unit_numerical_value = int(resp[1])
            unit_label = resp[2]
            units[label] = {
                'unit_numerical_value': unit_numerical_value,
                'unit_label': unit_label
            }
        return units

    
    @property
    def total_mass_conversion(self):
        """
        Get the current total mass conversion factor for the gas formula.

        Returns:
            The conversion factor for the current gas formula.
        """
        current_gas = self.gas['formula']
        items = list(self.gas_dict[current_gas].items())
        if len(items) < 2:
            return None
        return items[1]  # (key, value) tuple

    def set_total_mass_conversion(self, conversion_name, factor):
        current_gas = self.gas['formula']
        self.gas_dict[current_gas] = {k: v for k, v in self.gas_dict[current_gas].items() if k == 'number'}
        self.gas_dict[current_gas][conversion_name] = factor  # Update the conversion factor for H2

    ### TARING ###
    @property
    def tare(self):
        # poll the current status
        return self.poll()
    
    @tare.setter
    def tare(self, which):
        """
        Perform a tare operation based on the string provided:
          - "flow"      → send 'V'
          - "pressure"  → send 'P'
          - "absolute"  → send 'PC'
        """

        key = which.strip().lower()
        if key == "flow":
            cmd = "V"       # Flow‐tare
        elif key == "pressure":
            cmd = "P"       # Gauge/differential‐pressure tare
        elif key == "absolute":
            cmd = "PC"      # Absolute‐pressure (barometer) tare
        else:
            raise ValueError("Invalid tare type. Choose 'flow', 'pressure', or 'absolute'.")

        self._send_command(cmd)

    ### CLOSE ###
    def close(self):
        '''Close the serial connection.'''
        if self.ser.is_open:
            self.ser.close()


if __name__=='__main__':

    FC=Controller()
    print(FC._send_command('LCG 0'))
    print(FC._send_command('FPF 5 66'))

    t_start=time.time()

    while True:
        try:
            print('--------------------')
            t_now=time.time()
            print(f'{t_now-t_start:.2f}')
            data = FC.poll()    

            print(f'Pressure: {data["P"][0]:.2f} {data["P"][1]}')
            print(f'Temperature: {data["T"][0]:.2f} {data["T"][1]}')
            print(f'Volumetric Flow: {data["V"][0]:.2f} {data["V"][1]}')
            print(f'Mass Flow: {data["M"][0]:.2f} {data["M"][1]}')
            print(f'Setpoint: {data["S"][0]:.2f} {data["S"][1]}')
            print(f'Accumulated Mass: {data["A"][0]:.2f} {data["A"][1]}')
            print(f'Gas: {data["G"]}')

            
            FC.setpoint = 0.0001480

            time.sleep(1)
        except:
            FC.close()
            break