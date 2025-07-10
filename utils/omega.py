import board
import busio
import adafruit_ads1x15.ads1115 as ADS
import adafruit_mcp4725 as DAC
from adafruit_ads1x15.analog_in import AnalogIn
import time
from utils.relay import RelayBoard, RelayControl


class ADS1115:
    def __init__(self,addr):
        bus=busio.I2C(board.SCL,board.SDA)
        self.ads=ADS.ADS1115(
            bus,
            address=addr,
            gain=2/3,
            data_rate=64
            )
        self.a0=AnalogIn(self.ads,ADS.P0)
        self.a1=AnalogIn(self.ads,ADS.P1)
        self.a2=AnalogIn(self.ads,ADS.P2)

    @property
    def signal(self):
        return {
            0: self.a0.voltage,
            1: self.a1.voltage,
            2: self.a2.voltage,
        }

class MCP4725:
    def __init__(self, addr):
        bus = busio.I2C(board.SCL, board.SDA)
        self.dac = DAC.MCP4725(bus, address=addr)

    def set_voltage(self, voltage):
        value = int((voltage / 5.0) * 65535)
        self.dac.value = value    

class OmegaFM:
    def __init__(self, addr):
        self.ads = ADS1115(addr)
    def flow(self, pinout):
        voltage = self.ads.signal[pinout]
        # 0-5V corresponds to 0-10 L/min, so scale linearly
        flow_rate = (voltage / 5.0) * 10.0
        return voltage
    
class OmegaFC:
    def __init__(self, addrADC, addrDAC):
        self.ads = ADS1115(addrADC)
        self.dac = MCP4725(addrDAC)

    @property
    def flow(self):
        voltage = self.ads.signal[2]
        # 0-5V corresponds to 0-10 L/min, so scale linearly
        flow_rate = (voltage / 5.0) * 10.0
        return voltage

    @flow.setter
    def set_flow(self, flow_rate, ramp_rate=None):
        current_flow = self.flow

        if ramp_rate is None or abs(flow_rate - current_flow) < 1e-3:
            # No ramping, set directly
            voltage = (flow_rate / 10.0) * 5.0
            self.dac.set_voltage(voltage)
            print(f'Setting flow to {flow_rate:.2f} which is {voltage:.3f} V')
        else:
            # Ramp in small steps
            step_time = 0.05  # seconds per step
            step_flow = ramp_rate * step_time
            steps = int(abs(flow_rate - current_flow) / step_flow)
            direction = 1 if flow_rate > current_flow else -1
            for i in range(steps):
                intermediate_flow = current_flow + direction * step_flow * (i + 1)
                voltage = (intermediate_flow / 10.0) * 5.0
                self.dac.set_voltage(voltage)
                time.sleep(step_time)
            # Set final value
            voltage = (flow_rate / 10.0) * 5.0
            self.dac.set_voltage(voltage)
            print(f'Ramped flow to {flow_rate:.2f} which is {voltage:.3f} V')

if __name__=='__main__':
    
    FM = OmegaFM(addr=0x4B)
    # FC = OmegaFC(addrADC=0x4B, addrDAC=0x60)
    t_start = time.time()
    relay_board = RelayBoard()
    svi = RelayControl(relay_board=relay_board,relay='R4')
    svo = RelayControl(relay_board=relay_board,relay='R3')
    svi.on()
    svo.on()
    while True:
        try:
            string = (
                f'{time.time()-t_start:.3f} \n'
                f'FM1:  {FM.flow(0):.3f} \n'
                f'FM2:  {FM.flow(1):.3f} \n'
                # f'FC1:  {FC.flow():.3f} \n'
            )
            print(string)
            # flow = 5.0
            while time.time()-t_start<1:
                pass
        except KeyboardInterrupt:
            break
        