import board
import busio
import adafruit_mcp4725 as DAC
from adafruit_ads1x15.analog_in import AnalogIn
from utils.sensors import ADS1115
import time

class MCP4725:
    def __init__(self, addr):
        bus = busio.I2C(board.SCL, board.SDA)
        self.dac = DAC.MCP4725(bus, address=addr)

    def set_voltage(self, voltage):
        value = int((voltage / 5.0) * 65535)
        self.dac.value = value    

class Omega:
    def __init__(self, addr, max_flow, unit='L/min'):
        self.ads = ADS1115(addr)
        self.max_flow = max_flow
        self.unit = unit
    def flow(self, pinout):
        voltage = self.ads.voltage[pinout]
        # 0-5V corresponds to linearly
        flow_rate = (voltage / 5.0) * self.max_flow
        return (flow_rate, self.unit)
    
class OmegaFC:
    def __init__(self, addr, max_flow, unit):
        self.FC = Omega(addr, max_flow=max_flow, unit=unit)
        self.dac = MCP4725(0x60)  # DAC address for flow control
        self.max_flow = max_flow  # unit
        self.unit = unit
    def flow(self):
        return self.FC.flow(2)
    def set_flow(self, flow_rate, ramp_rate=None):
        current_flow = self.flow
        if ramp_rate is None or abs(flow_rate - current_flow) < 1e-3:
            # No ramping, set directly
            voltage = (flow_rate / self.max_flow) * 5.0
            self.dac.set_voltage(voltage)
            print(f'Setting flow to {flow_rate:.2f} {self.unit} which is {voltage:.3f} V')
        else:
            # Ramp in small steps
            step_time = 0.05  # seconds per step
            step_flow = ramp_rate * step_time
            steps = int(abs(flow_rate - current_flow) / step_flow)
            direction = 1 if flow_rate > current_flow else -1
            for i in range(steps):
                intermediate_flow = current_flow + direction * step_flow * (i + 1)
                voltage = (intermediate_flow / self.max_flow) * 5.0
                self.dac.set_voltage(voltage)
                time.sleep(step_time)
            # Set final value
            voltage = (flow_rate / self.max_flow) * 5.0
            self.dac.set_voltage(voltage)
            print(f'Ramped flow to {flow_rate:.2f} {self.unit} which is {voltage:.3f} V')

class FMA1820A(Omega):
    def __init__(self, addr):
        super().__init__(addr, max_flow=10, unit='L/min')
        self.model = 'FMA1820A (METER | 0-10L/min)'

class FMA5508A(OmegaFC):
    def __init__(self, addr):
        super().__init__(addr, max_flow=100, unit='mL/min')
        self.model = 'FMA5508A (CONTROLLER | 0-100mL/min)'

class FMA5520A(OmegaFC):
    def __init__(self, addr):
        super().__init__(addr, max_flow=10, unit='L/min')
        self.model = 'FMA5520A (CONTROLLER | 0-10L/min)'

if __name__=='__main__':
    
    FM = FMA1820A(addr=0x4B)
    FC = FMA5520A(addr=0x4B)
    t_start = time.time()
    
    while True:
        try:
            string = (
                f'{time.time()-t_start:.3f} \n'
                f'FM:  {FM.flow(0)[0]:.3f} {FM.flow(0)[1]} \n'
                f'FC:  {FC.flow()[0]:.3f} {FC.flow()[1]} \n'
            )
            print(string)
            while time.time()-t_start<1:
                pass
        except KeyboardInterrupt:
            break
        