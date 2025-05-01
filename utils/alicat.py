import serial
import time

class Controller:

    # Next steps:
        # gas_dict information including conversions
        # ramp rate to avoid TMF error
        # totalizer configuration

    # Constants only for hydrogen, be careful when using other gases
    # Should incorporate into gas_dict
    H2_SCCM2G=8.988e-5
    H2_SLPM2GPS=0.08988/60

    def __init__(self, port='/dev/ttyUSB0', baudrate=19200, address='A', timeout=1):
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
        self._send_command('TC 1 -1 0 -1 7 0') # Improve with custom totalizer functionality (for now sets up TC1)
        self._send_command('TC 2 1') # Polling relies on knowing only one totalizer is active
        self.gas_dict={'H2':6,'O2':11}
        self.gas='H2'

    def _send_command(self, command):
        full_command = f'{self.address}{command}\r'.encode('utf-8')
        self.ser.write(full_command)
        time.sleep(0.1)
        return self.ser.readline().decode('utf-8').strip().split()

    ### POLLING ###

    def poll(self):
        '''Poll flow, pressure, and temperature.'''
        data=self._send_command('')
        data_dict={
            'U':data[0],
            'P':float(data[1]), # Downstream pressure (barA)
            'T':float(data[2]), # Gas temperature (C)
            'V':float(data[3]), # Volumetric flow (SLPM)
            'M':float(data[4]), # Mass flow (g/s)
            'S':float(data[5]), # Mass flow setpoint (g/s)
            'A':float(data[6])*self.__class__.H2_SCCM2G, # Accumulated mass (g)
            'G':data[7],
            'E':[]
        }
        for code in data[8:]:
            data_dict['E'].append(code)
        return data_dict

    ### CONTROL ###

    @property
    def setpoint(self):
        resp=self._send_command('LS')
        return float(resp[1])

    @setpoint.setter
    def setpoint(self,value):
        self._send_command(f'LS {value}')

    ### GAS ###
    
    @property
    def gas(self):
        resp=self._send_command(f'GS')
        return {'number':int(resp[1]),'formula':resp[2],'name':resp[3]}
    
    @gas.setter
    def gas(self,formula):
        if formula in self.gas_dict:
            number=self.gas_dict[formula]
        else:
            number=6 # H2 default
            printout=(
                f'{formula} is invalid\n'
                f'Setting to default: H2\n'
                f'Acceptable gases:\n'
            )
            for k,v in self.gas_dict.items():
                printout+=f'\t{k}\n'
            print(printout)
        self._send_command(f'G {number}')

    ### TOTALIZER ###

    def totalizer_reset(self,num=1):
        '''Reset totalizer either num 1 or 2'''
        t_num=int(sorted([1,num,2])[1])
        self._send_command(f'T {t_num}')

    ### CLOSE ###

    def close(self):
        '''Close the serial connection.'''
        if self.ser.is_open:
            self.ser.close()

if __name__=='__main__':

    FC=Controller()
    FC.totalizer_reset()
    # print(FC._send_command('GS'))
    print(FC.gas)
    FC.gas='ABC'
    print(FC.gas)
    
    while True:
        try:
            print(FC.poll())
            time.sleep(1)
        except:
            FC.close()
            break
