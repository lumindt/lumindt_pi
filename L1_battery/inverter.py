import can
import time
from datetime import datetime, timedelta, timezone
import subprocess


'''
Improvements
- Function for changing EEPROM
- Develop desired abstracted control framework
- Eliminate threading
'''

class Device:

    def __init__(self,bus,addr=0,debug=False):
        self.bus=bus
        self.recv_ID=0x000C0400+addr
        self.send_ID=0x000C0500+addr
        self.debug=debug

        self._mode=0
        self._input_power=1000
        self._printout={}
        self._charge={}
        self._fault={}

        self.EEPROM()
        self.setup()
        
    # ===== UTILS =============================================================
        
    def _send(self,code,values=[]):
        msg=can.Message(
            is_extended_id=True,
            arbitration_id=self.send_ID,
            data=list(code.to_bytes(2,'little'))+values,
            is_rx=False
            )
        try:
            if self.debug: print(msg)
            self.bus.send(msg)
        except:
            print('Message NOT sent')

    def _recv(self,timeout=1.0):
        try:
            msg=self.bus.recv(timeout=timeout)
            if self.debug: print(msg)
        except:
            print('Message NOT received')
            return None
        if msg==None:
            return None
        addr=msg.arbitration_id-self.recv_ID
        code=hex(int.from_bytes(msg.data[:2],'little'))
        values=msg.data[2:]
        return [addr,code,values]

    def _get(self,code):
        self._send(code=code)
        resp=self._recv()
        time.sleep(0.1)
        if self.debug:
            # print(f'Message Name:  {resp.name}')
            print(f'Command Check: {hex(code)} == {resp[1]}')
        return resp[2]

    def _set(self,code,value,factor,vmin,vmax):
        try:
            data=list(int(sorted([vmin,value,vmax])[1]/factor).to_bytes(2,'little'))
            self._send(code=code,values=data)
        except:
            print(f'INVALID ENTRY: code {hex(code)}')

    # ===== READ VALUE ========================================================

    # ----- INPUT -----

    def READ_VIN(self):
        '''AC INPUT VOLTAGE'''
        regs=self._get(code=0x0050)
        return 0.1*int.from_bytes(regs,'little')

    def READ_IIN(self):
        '''AC INPUT CURRENT'''
        regs=self._get(code=0x0053)
        return 0.1*int.from_bytes(regs,'little')

    def READ_FIN(self):
        '''AC INPUT FREQUENCY'''
        regs=self._get(code=0x0056)
        return 0.01*int.from_bytes(regs,'little')

    # ----- OUTPUT -----

    def READ_VOUT(self):
        '''AC OUTPUT VOLTAGE'''
        regs=self._get(code=0x0108)
        return 0.1*int.from_bytes(regs,'little')

    def READ_IOUT(self):
        '''AC OUTPUT CURRENT'''
        regs=self._get(code=0x012B)
        return 0.1*int.from_bytes(regs,'little')

    def READ_FOUT(self):
        '''AC OUTPUT FREQUENCY'''
        regs=self._get(code=0x0105)
        return 0.01*int.from_bytes(regs,'little')

    def READ_PCNT(self):
        '''AC OUTPUT LOAD PERCENTAGE'''
        regs=self._get(code=0x010B)
        return int.from_bytes(regs,'little') # Percent

    def READ_WATT(self):
        '''AC OUTPUT WATTAGE'''
        hi=self._get(code=0x010E)
        lo=self._get(code=0x010F)
        return 0.1*(int.from_bytes(hi,'little')<<8 | int.from_bytes(lo,'little'))

    def READ_VA(self):
        '''AC OUTPUT APPARENT POWER'''
        hi=self._get(code=0x0114)
        lo=self._get(code=0x0115)
        return 0.1*(int.from_bytes(hi,'little')<<8 | int.from_bytes(lo,'little'))

    # ----- BATTERY -----

    def READ_VBAT(self):
        '''BATTERY VOLTAGE'''
        regs=self._get(code=0x011A)
        return 0.01*int.from_bytes(regs,'little')

    def READ_IBAT(self):
        '''BATTERY CURRENT'''
        regs=self._get(code=0x011B)
        if self.debug: print(regs)
        return 0.01*int.from_bytes(regs,'little',signed=True)

    # ----- MISC -----

    def READ_TMP(self):
        '''INTERNAL TEMPERATURE'''
        regs=self._get(code=0x0062)
        return 0.1*int.from_bytes(regs,'little')

    # ===== READ/WRITE VALUE ==================================================

    # ----- CHARGE CURVE -----

    def CURVE_CC(self,value=None):
        '''[EEPROM] CHARGE CURVE CONSTANT CURRENT SETTING'''
        if value == None:
            regs=self._get(code=0x00B0)
            return 0.01*int.from_bytes(regs,'little')
        else:
            self._set(code=0x00B0,value=value,factor=0.01,vmin=14,vmax=70)

    def CURVE_CC_TIMEOUT(self,value=None):
        '''CHARGE CURVE CONSTANT CURRENT TIMEOUT (MINUTES)'''
        if value == None:
            regs=self._get(code=0x00B5)
            return int.from_bytes(regs,'little')
        else:
            self._set(code=0x00B5,value=value,factor=1,vmin=60,vmax=64800)

    def CURVE_CV(self,value=None):
        '''[EEPROM] CHARGE CURVE CONSTANT VOLTAGE SETTING'''
        if value == None:
            regs=self._get(code=0x00B1)
            return 0.01*int.from_bytes(regs,'little')
        else:
            self._set(code=0x00B1,value=value,factor=0.01,vmin=48,vmax=56)

    def CURVE_CV_TIMEOUT(self,value=None):
        '''CHARGE CURVE CONSTANT VOLTAGE TIMEOUT (MINUTES)'''
        if value == None:
            regs=self._get(code=0x00B6)
            return int.from_bytes(regs,'little')
        else:
            self._set(code=0x00B6,value=value,factor=1,vmin=60,vmax=64800)

    def CURVE_FV(self,value=None):
        '''[EEPROM] CHARGE CURVE FLOAT VOLTAGE SETTING'''
        if value == None:
            regs=self._get(code=0x00B2)
            return 0.01*int.from_bytes(regs,'little')
        else:
            self._set(code=0x00B2,value=value,factor=0.01,vmin=40,vmax=60)

    def CURVE_FV_TIMEOUT(self,value=None):
        '''CHARGE CURVE FLOAT VOLTAGE TIMEOUT (MINUTES)'''
        if value == None:
            regs=self._get(code=0x00B7)
            return int.from_bytes(regs,'little')
        else:
            self._set(code=0x00B7,value=value,factor=1,vmin=60,vmax=64800)

    def CURVE_TC(self,value=None):
        '''[EEPROM] CHARGE CURVE FLOAT CROSSOVER (TAPER) CURRENT SETTING'''
        if value == None:
            regs=self._get(code=0x00B3)
            return 0.01*int.from_bytes(regs,'little')
        else:
            self._set(code=0x00B3,value=value,factor=0.01,vmin=1.4,vmax=21)

    # ----- BATTERY TRIGGERS -----

    def BAT_ALM_VOLT(self,value=None):
        '''[EEPROM] BATTERY LOW VOLTAGE ALARM'''
        if value == None:
            regs=self._get(code=0x00B9)
            return 0.01*int.from_bytes(regs,'little')
        else:
            self._set(code=0x00B9,value=value,factor=0.01,vmin=37.6,vmax=50)

    def BAT_SHDN_VOLT(self,value=None):
        '''[EEPROM] BATTERY LOW VOLTAGE SHUTDOWN'''
        if value == None:
            regs=self._get(code=0x00BA)
            return 0.01*int.from_bytes(regs,'little')
        else:
            self._set(code=0x00BA,value=value,factor=0.01,vmin=36.8,vmax=48)

    def BAT_RCHG_VOLT(self,value=None):
        '''[EEPROM] BATTERY RECHARGE THRESHOLD VOLTAGE'''
        if value == None:
            regs=self._get(code=0x00BB)
            return 0.01*int.from_bytes(regs,'little')
        else:
            self._set(code=0x00BB,value=value,factor=0.01,vmin=36.8,vmax=60)

    # ===== CONFIG ============================================================

    def CURVE_CONFIG(self,**new_config):
        '''
        HI  [  0  |  0  |  0  |  0  |  0  |FVTOE|CVTOE|CCTOE]
        LO  [  0  | STGS|  0  |  0  |    TCS    |    CUVS   ]
        '''
        code=0x00B4
        [lo,hi]=self._get(code=code)
        config_dict={
            'CUVS':     (lo & 0b00000011),      # Charge Curve Preset
            'TCS':      (lo & 0b00001100) >> 2, # Temperature Compensation
            'STGS':     (lo & 0b01000000) >> 6, # 2 or 3 Stage Charging
            'CCTOE':    (hi & 0b00000001),      # CC Timeout Enable
            'CVTOE':    (hi & 0b00000010) >> 1, # CV Timeout Enable
            'FVTOE':    (hi & 0b00000100) >> 2, # FV Timeout Enable
        }
        if new_config=={}:
            return config_dict
        else:
            config_dict |= new_config
            new_lo=config_dict['CUVS'] | config_dict['TCS']<<2 | config_dict['STGS']<<6
            new_hi=config_dict['CCTOE'] | config_dict['CVTOE']<<1 | config_dict['FVTOE']<<2
            self._send(code=code,values=[new_lo,new_hi])
            return config_dict

    def SYSTEM_CONFIG(self,**new_config):
        '''
        HI  [  0  |  0  |  0  |  0  |  0  |EEP_OFF| EEP_CONFIG]
        LO  [  0  |  0  |  0  |  0  |  0  |   0   |  0  |  0  ]
        '''
        code=0x00C2
        [lo,hi]=self._get(code=code)
        config_dict={
            'EEP_CONFIG':   (hi & 0b00000011),      # Write Time Delay
            'EEP_OFF':      (hi & 0b00000100) >> 2, # Disable Writing
        }
        if new_config=={}:
            return config_dict
        else:
            config_dict |= new_config
            new_lo=0
            new_hi=config_dict['EEP_CONFIG'] | config_dict['EEP_OFF']<<2
            self._send(code=code,values=[new_lo,new_hi])
            return config_dict

    def INV_OPERATION(self,**new_config):
        '''
        HI  [  0  |  0  |  0  |  0  |  0  |   0   |  0  |   0   ]
        LO  [  0  |  0  |  0  |  0  |  0  | CHG_EN|OP_EN|OP_CTRL]
        '''
        code=0x0100
        [lo,hi]=self._get(code=code)
        config_dict={
            'OP_CTRL':  (lo & 0b00000001),      # Enable Output (Requires OP_EN)
            'OP_EN':    (lo & 0b00000010) >> 1, # Enable OP_CTRL
            'CHG_EN':   (lo & 0b00000100) >> 2, # Enable Charger
        }
        if new_config=={}:
            return config_dict
        else:
            config_dict |= new_config
            new_lo=config_dict['OP_CTRL'] | config_dict['OP_EN']<<1 | config_dict['CHG_EN']<<2
            new_hi=0
            self._send(code=code,values=[new_lo,new_hi])
            return config_dict

    def INV_CONFIG(self,**new_config):
        '''
        HI  [  0  |  0  |  0  |  0  |  0  |  0  |  0  |  0  ]
        LO  [  0  |  0  |  0  |  0  |  0  |  0  |  INV_PRIO ]
        '''
        code=0x0101
        [lo,hi]=self._get(code=code)
        config_dict={
            'INV_PRIO':  (lo & 0b00000011),     # Energy Saving Mode
        }
        if new_config=={}:
            return config_dict
        else:
            config_dict |= new_config
            new_lo=config_dict['INV_PRIO']
            new_hi=0
            self._send(code=code,values=[new_lo,new_hi])
            return config_dict

    # ===== STATUS ============================================================

    def CHG_STATUS(self):
        '''
        HI  [FVTOF|CVTOF|CCTOF|  0  |  0  |NTCER|  0  |  0  ]
        LO  [  0  |  0  |  0  |  0  | FVM | CVM | CCM |FULLM]
        '''
        code=0x00B8
        [lo,hi]=self._get(code=code)
        config_dict={
            'FULLM':    (lo & 0b00000001),      # Battery Full
            'CCM':      (lo & 0b00000010) >> 1, # Constant Current Mode
            'CVM':      (lo & 0b00000100) >> 2, # Constant Voltage Mode
            'FVM':      (lo & 0b00001000) >> 3, # Float Voltage Mode
            'NTCER':    (hi & 0b00000100) >> 2, # Temperature Compensation On
            'CCTOF':    (hi & 0b00100000) >> 5, # CC Timeout Flag
            'CVTOF':    (hi & 0b01000000) >> 6, # CV Timeout Flag
            'FVTOF':    (hi & 0b10000000) >> 7, # FV Timeout Flag
        }
        return config_dict

    def INV_STATUS(self):
        '''
        HI  [  0  |     0     |   0   |    0    |   0   |   0   | INV_PHASE ]
        LO  [  0  |Bat_Low_ALM| SAVING| SOLAR_EN| CHG_ON| UTI_OK| BYP | INV ]
        '''
        code=0x011D
        [lo,hi]=self._get(code=code)
        config_dict={
            'INV':          (lo & 0b00000001),      # Inverter Mode
            'BYP':          (lo & 0b00000010) >> 1, # Bypass Mode
            'UTI_OK':       (lo & 0b00000100) >> 2, # Utility Power Connected
            'CHG_ON':       (lo & 0b00001000) >> 3, # Charger On
            'SOLAR_EN':     (lo & 0b00010000) >> 4, # Solar Charger On
            'SAVING':       (lo & 0b00100000) >> 5, # Energy Saving Mode
            'Bat_Low_ALM':  (lo & 0b01000000) >> 6, # Battery Low Flag
            'INV_PHASE':    (hi & 0b00000011),      # Inverter Phase
        }
        return config_dict

    def INV_FAULT(self):
        '''
        HI  [   0   |  0  |   0   |INV_Fault|Bat_OVP|Bat_UVP|FAN_FAIL|  SHDN  ]
        LO  [EEP_Err| SCP |INV_OVP| INV_UVP |  OTP  |OLP_150| OLP_115| OLP_100]
        '''
        code=0x011E
        [lo,hi]=self._get(code=code)
        config_dict={
            'OLP_100':      (lo & 0b00000001),      # >100% Power Overload
            'OLP_115':      (lo & 0b00000010) >> 1, # >115% Power Overload
            'OLP_150':      (lo & 0b00000100) >> 2, # >150% Power Overload
            'OTP':          (lo & 0b00001000) >> 3, # Over Temperature
            'INV_UVP':      (lo & 0b00010000) >> 4, # Inverter Under Voltage
            'INV_OVP':      (lo & 0b00100000) >> 5, # Inverter Over Voltage
            'SCP':          (lo & 0b01000000) >> 6, # Short Circuit
            'EEP_Err':      (lo & 0b10000000) >> 7, # EEPROM Error
            'SHDN':         (hi & 0b00000001),      # System Shutdown
            'FAN_FAIL':     (hi & 0b00000010) >> 1, # Fan Error
            'Bat_UVP':      (hi & 0b00000100) >> 2, # Battery Under Voltage
            'Bat_OVP':      (hi & 0b00001000) >> 3, # Battery Over Voltage
            'INV_Fault':    (hi & 0b00010000) >> 4, # Inverter Fault
        }
        return config_dict

    # ===== CUSTOM FUNCTIONS ==================================================

    # ----- STARTUP -----

    def EEPROM(self):
        # Disable EEPROM; set immediate EEPROM saving when enabled
        self.SYSTEM_CONFIG(EEP_OFF=1,EEP_CONFIG=0)
        # Check desired settings
        # Be careful about changing presets, if the preset value is out of the range, it 
        preset=[
            self.CURVE_FV()==54.6,
            self.CURVE_TC()==7,
            self.BAT_ALM_VOLT()==50,
            self.BAT_SHDN_VOLT()==48,
            self.BAT_RCHG_VOLT()==50,
        ]
        # Conditional actions
        if all(preset):
            print('EEPROM already set')
        else:
            print('Setting EEPROM...')
            self.CURVE_FV(value=54.6)
            self.CURVE_TC(value=7)
            self.BAT_ALM_VOLT(value=50)
            self.BAT_SHDN_VOLT(value=48)
            self.BAT_RCHG_VOLT(value=50)
            # Turn on EEPROM briefly to save desired settings
            self.SYSTEM_CONFIG(EEP_OFF=0)
            time.sleep(0.1)
            self.SYSTEM_CONFIG(EEP_OFF=1)
            time.sleep(0.1)
            print('EEPROM settings saved')
            print('Warning: Do not save to EEPROM too often - Limited saves')

    def setup(self):
        # Two stage charging only
        self.CURVE_CONFIG(STGS=1)
        # Enable output control; disable output and charging
        self.INV_CONFIG(OP_EN=1,OP_CTRL=0,CHG_EN=0)
        # Set initial input power
        ibat=self._input_power/56
        self.CURVE_CC(value=ibat)
        self.CURVE_CV(value=56)

    # ----- Operation -----

    def mode(self,new_mode=0):
        if new_mode==1: # BATTERY CHARGE
            self.INV_OPERATION(OP_EN=1,OP_CTRL=0)
            time.sleep(0.2)
            self.INV_OPERATION(CHG_EN=1)
            self._mode=new_mode
        elif new_mode==2: # BATTERY DISCHARGE AND BYPASS
            self.INV_OPERATION(CHG_EN=0)
            time.sleep(0.2)
            self.INV_OPERATION(OP_EN=1,OP_CTRL=1)
            self._mode=new_mode
        else: # OFF
            self.INV_OPERATION(CHG_EN=0,OP_EN=1,OP_CTRL=0)
            self._mode=0

    # ----- Power Thread -----

    def update(self):
        vbat=self.READ_VBAT()
        ibat=self.READ_IBAT()
        pbat=vbat*ibat
        mode=self._mode
        chg=self.CHG_STATUS()
        self._printout|=(
            chg|
            self.INV_STATUS()|
            {}
        )
        cvm=chg['CVM']
        ccm=chg['CCM']
        flm=chg['FULLM']
        self._printout |= {
            'MODE':mode,
            'VBAT':vbat,
            'IBAT':ibat,
            'PBAT':pbat,
        }
        if mode==1:
            p_desired=self._input_power
            if p_desired==0:
                p_error=0
            else:
                p_error=(p_desired-pbat)/p_desired
            self._printout |= {
                'PCMD':p_desired,
                'PERR':p_error,
            }
            if abs(p_error) > 0.01 and not flm:
                if cvm:
                    ides=p_desired/vbat
                    vdes=p_desired/ides if ides!=0 else 52 # BE CAREFUL NOT TO DIVIDE BY ZERO
                    self.CURVE_CV(value=round(vdes,2))
                    # self.CURVE_CC(value=ibat)
                elif ccm:
                    self.CURVE_CC(value=round(p_desired/vbat,2))
                    # self.CURVE_CV(value=vbat)
                time.sleep(5)
        else:
            self._printout |= {
                'PCMD':0,
                'PERR':0,
            }

    def close(self):
        self.bus.shutdown()
        print('Ending')

def printout(d=None):
    string='\n----------\n'
    string+=f'{datetime.now(timezone(timedelta(hours=-7))).strftime("%H:%M:%S.%f")[:-3]}\n'
    string+='----------\n'
    for k,v in d.items():
        string+=f'{k: >12}: {v:<10.3f}\n'
    string+='----------'
    print(string)
 

if __name__ == '__main__':
    subprocess.run("sudo ip link set can1 down", shell=True, check=True) # Set CAN1 down
    subprocess.run("sudo ip link set can1 up type can bitrate 250000", shell=True, check=True) # Set CAN1 up
    bus = can.interface.Bus(interface='socketcan', channel='can1', bitrate=250000) # Set up CAN bus
    dev=Device(bus=bus,debug=False)
    start=time.time()
    try:
        while(True):
            try:
                dev.update()
                printout(dev._printout)
                time.sleep(1)
            except KeyboardInterrupt:
                cmd_string=(
                    '\nChange mode?\n'
                    f'Current mode: {dev._mode}\n'
                    '0 -> Standby\n'
                    '1 -> Charge\n'
                    '2 -> Discharge\n'
                    'Press ENTER to end script\n'
                )
                new_mode=int(input(cmd_string))
                if new_mode==1: 
                    try:
                        power_string=(
                            '\nNew Charge Power (W)?\n\n'
                            f'{"MIN": ^10}|{"COMMAND": ^10}|{"MAX": ^10}\n'
                            f'{"":-^10}|{"":-^10}|{"":-^10}\n'
                            f'{57.6*14: ^10}|{dev._input_power: ^10.2f}|{4200: ^10}\n\n'
                            'New Entry? (Press ENTER to maintain)\n'
                        )
                        new_power=int(input(power_string))
                        dev._input_power=new_power
                    except:
                        print(f'\nMaintain Power: {dev._input_power}\n')
                dev.mode(new_mode=new_mode)
    except KeyboardInterrupt:
        print('\nClosing')
    except Exception as e:
        print(e)
    finally:
        dev.mode(new_mode=0)
        time.sleep(0.2)
        dev.close()

