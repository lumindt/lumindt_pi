import can
import cantools
import time
import utils
import config
import threading



class FuelCellController:
    def __init__(self, debug=False):
        utils.canup_fuel_cell()  # Set up the CAN bus at start on can1

        self.bus = can.interface.Bus(channel='can0', interface='socketcan')  # Set up the CAN bus for FC

        self.db = cantools.database.load_file('horizon_fc/FCU.dbc')
        self.debug = debug
        self.name = 'VCU_1'
        self.template = self.db.get_message_by_name(self.name)
        self.id = self.template.frame_id
        self.raw = b'\x00\x00\x00\x00\x00\x00\x00\x00'
        self.data = self.template.decode(self.raw)
        self.message = can.Message(arbitration_id=self.id, data=self.raw)
        self.init = self.message
        if self.debug:
            print(self.message)
        self.task = self.bus.send_periodic(self.message, 0.1)

        # Initialize dictionaries
        self.FC01 = {}
        self.FC02 = {}
        self.FC03 = {}
        self.FC04 = {}
        self.FC05 = {}

        # Start the background thread to update the dictionaries
        self.running = True
        self.update_thread = threading.Thread(target=self._update_dictionaries)
        #make daemon
        self.update_thread.daemon = True
        self.update_thread.start()

    def _modify(self, signal, value):
        self.data[signal] = value
        self.raw = self.template.encode(self.data)
        self.message = can.Message(arbitration_id=self.id, data=self.raw)
        if self.debug:
            print(self.template.decode(self.message.data))
        self.task.modify_data(self.message)
        return

    def _LIFO(self, name, time_window=0.05):
        message = self.db.get_message_by_name(name)
        id = message.frame_id
        msg = self.bus.recv()
        while time.time() - msg.timestamp > time_window or msg.arbitration_id != id:
            msg = self.bus.recv()
        if not msg:
            print('No Message')
        return msg

    def read(self, name, target_dict):
        msg = self._LIFO(name)
        if msg:
            decoded_data = self.db.decode_message(msg.arbitration_id, msg.data)
            if self.debug:
                print(f'{hex(msg.arbitration_id)}\t{decoded_data}')
            target_dict.update(decoded_data)
            return decoded_data
        return None

    def _update_dictionaries(self):
        while self.running:
            try:
                self.read('FCU_01', self.FC01)
                self.read('FCU_02', self.FC02)
                self.read('FCU_03', self.FC03)
                self.read('FCU_04', self.FC04)
                self.read('FCU_05', self.FC05)
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error in update thread: {e}")
                self.close()
                break

    def fuelcell_on(self, switch: bool): self._modify('VCU1_StartFCS', int(switch))
    def set_voltage(self, value: float): self._modify('VCU1_FCSMaxOutVolt', value)
    def set_power(self, value: float): self._modify('VCU1_ReqPower', value)
    def set_pumpspeed(self, value: float): self._modify('VCU1_VehicleSpeed', value)
    def system_on(self, switch: bool): self._modify('VCU1_OnVoltageActive', int(switch))
    def voltage_on(self, switch: bool): self._modify('VCU1_HighVoltStatus', int(switch))
    def is_running(self): return self.data['VCU1_StartFCS']
    def get_pumpspeed(self): return self.data['VCU1_VehicleSpeed']
    def get_target_voltage(self): return self.data['VCU1_FCSMaxOutVolt']
    def get_target_power(self): return self.data['VCU1_ReqPower']

    def get_system_output_power(self):
        key = 'FCU1_SystemOutputPower'
        return self.FC01[key] if key in self.FC01 else None
    
    def get_system_output_voltage(self):
        key = 'FCU2_SystemOutputVoltage'
        return self.FC02[key] if key in self.FC02 else None

    #get phase
    def get_phase(self):
        key = 'FCU1_Phase'
        #get phase number and then get the phase name from the dictionary
        return config.PHASE_DICTIONARY[self.FC01[key]] if key in self.FC01 else None
    
    #get fault codes
    def get_fault_codes(self):
        key = 'FCU1_FaultCode'
        return self.FC01[key] if key in self.FC01 else None

    #get FCU2_FC_Power
    def get_fc_power(self):
        key = 'FCU2_FC_Power'
        return self.FC02[key] if key in self.FC02 else None
    
    def get_system_power(self):
        key = 'FCU1_SystemOutputPower'
        return self.FC01[key] if key in self.FC01 else None
    
    def close(self):
        self.running = False
        self.task.modify_data(self.init)
        time.sleep(1)
        self.bus.shutdown()
        print('Done.')

if __name__ == '__main__':
    fuel_cell = FuelCellController(debug=False)


    try:
        while True:
            #print all the data
            print(fuel_cell.FC01)
            print(fuel_cell.FC02)
            print(fuel_cell.FC03)
            print(fuel_cell.FC04)
            print(fuel_cell.FC05)
            # # time.sleep(5)
            # print(fuel_cell.is_running())
            # print(fuel_cell.get_pumpspeed())
            time.sleep(1)
    except KeyboardInterrupt:
        fuel_cell.close()