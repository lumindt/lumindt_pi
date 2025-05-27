import can
import cantools
import time
from datetime import datetime
import subprocess

# CAN bus setup: sudo ip link set can0 up type can bitrate 500000

'''
CAN EXT frames must add 0x80000000 to address in dbc file
DBC reader uses 32 bit address with 29 bit real address and 1 in MSB (32nd bit) spot
Really dumb and annoying
0x16900001 > 0x96900001 > 2526019585
0x16910001 > 0x96910001 > 2526085121
0x16920001 > 0x96920001 > 2526150657
0x16930001 > 0x96930001 > 2526216193
0x16940001 > 0x96940001 > 2526281729
0x16950001 > 0x96950001 > 2526347265
0x16960001 > 0x96960001 > 2526412801
0x16970001 > 0x96970001 > 2526478337
0x16980001 > 0x96980001 > 2526543873
0x16990001 > 0x96990001 > 2526609409
0x169a0001 > 0x969a0001 > 2526674945
0x169b0001 > 0x969b0001 > 2526740481
0x169c0001 > 0x969c0001 > 2526806017
0x169d0001 > 0x969d0001 > 2526871553
0x169e0001 > 0x969e0001 > 2526937089
0x169f0001 > 0x969f0001 > 2527002625
0x16a00001 > 0x96a00001 > 2527068161
0x16a10001 > 0x96a10001 > 2527133697
'''


class Device(can.Listener):

    def __init__(self,db,debug=False):
        self.db=db
        self.debug=debug
        self.store={}

    def on_message_received(self,msg):
        try:
            name=self.db.get_message_by_frame_id(msg.arbitration_id).name
            decoded=self.db.decode_message(name,msg.data)
            self.store[name]=decoded
        except:
            pass
            # print(f'{hex(msg.arbitration_id)} - {msg.arbitration_id}')

    def get_message(self,id):
        name=self.db.get_message_by_frame_id(id).name
        return self.store[name]

    def dump(self):
        screen=f'\n\n{"":-^60}\n'
        d=dict(sorted(self.store.items()))
        for m in d:
            screen+=f'{m:-^60}\n'
            for s in d[m]:
                screen+=f'{s: >5}: {d[m][s]: <8} | {hex(round(d[m][s])): <10} | {bin(round(d[m][s])): <20}\n'
        print(screen)

    def screen(self):
        wid=12
        screen=f'\n\n{"":-^{wid*5}}\n{datetime.now().strftime("%H:%M:%S.%f")[:-3]: ^{wid*5}}\n{"":-^{wid*5}}\n\n'
        values=self.store['Values']
        flags=self.store['Flags']
        limits=self.store['Limits']
        states=self.store['States']
        requests=self.store['Requests']
        # Values and Flags
        screen+=(
            '\n'
            f'{"VALUES": ^{wid}}{"": ^{wid}}{"FLAGS": ^{wid-2}}||{"PROTECT": ^{wid-1}}|{"ALARM": ^{wid-1}}|\n'
            f'{"":-^{wid}}{"": ^{wid}}{"":-^{wid}}{"":-^{wid}}{"":-^{wid}}\n'
        )
        screen+=(
            f'{"{:0.2f} V".format(values["Average_Module_Voltage"]): ^{wid}}'
            f'{"": ^{wid}}{"V+|V-": ^{wid-2}}||'
            f'{(str(flags["Protect_Over_Voltage"])+" | "+str(flags["Protect_Under_Voltage"])): ^{wid-1}}|'
            f'{(str(flags["Alarm_High_Voltage"])+" | "+str(flags["Alarm_Low_Voltage"])): ^{wid-1}}|\n'
        )
        screen+=(
            f'{"{:0.2f} A".format(values["Total_Current"]): ^{wid}}'
            f'{"": ^{wid}}{"I+|I-": ^{wid-2}}||'
            f'{(str(flags["Protect_Over_Current_Charge"])+" | "+str(flags["Protect_Over_Current_Discharge"])): ^{wid-1}}|'
            f'{(str(flags["Alarm_High_Current_Charge"])+" | "+str(flags["Alarm_High_Current_Discharge"])): ^{wid-1}}|\n'
        )
        screen+=(
            f'{"{:0.2f} C".format(values["Average_Cell_Temperature"]): ^{wid}}'
            f'{"": ^{wid}}{"T+|T-": ^{wid-2}}||'
            f'{(str(flags["Protect_Over_Temperature"])+" | "+str(flags["Protect_Under_Temperature"])): ^{wid-1}}|'
            f'{(str(flags["Alarm_High_Temperature"])+" | "+str(flags["Alarm_Low_Temperature"])): ^{wid-1}}|\n'
        )
        # Limits and States
        screen+=(
            '\n\n'
            f'{"STATES": ^{wid}}{"": ^{wid}}{"LIMITS": ^{wid-2}}||{"CHARGE": ^{wid-1}}|{"DISCHARGE": ^{wid-1}}|\n'
            f'{"":-^{wid}}{"": ^{wid}}{"":-^{wid}}{"":-^{wid}}{"":-^{wid}}\n'
        )
        screen+=(
            f'{"{:0.0f} % SOC".format(states["SOC"]): ^{wid}}'
            f'{"": ^{wid}}'
            f'{"VOLTAGE": ^{wid-2}}||'
            f'{"{:0.1f} V".format(limits["Charge_Voltage_Limit"]): ^{wid-1}}|'
            f'{"{:0.1f} V".format(limits["Discharge_Voltage_Limit"]): ^{wid-1}}|\n'
        )
        screen+=(
            f'{"{:0.0f} % SOH".format(states["SOH"]): ^{wid}}'
            f'{"": ^{wid}}'
            f'{"CURRENT": ^{wid-2}}||'
            f'{"{:0.1f} A".format(limits["Charge_Current_Limit"]): ^{wid-1}}|'
            f'{"{:0.1f} A".format(limits["Discharge_Current_Limit"]): ^{wid-1}}|\n'
        )
        # Requests
        screen+=(
            '\n\n'
            f'{"REQUESTS": ^{wid-2}}||{"FULL": ^{wid-1}}|{"FORCE": ^{wid-1}}|{"CHARGE": ^{wid-1}}|{"DISCHARGE": ^{wid-1}}|\n'
            f'{"":-^{wid}}{"":-^{wid}}{"":-^{wid}}{"":-^{wid}}{"":-^{wid}}\n'
        )
        screen+=(
            f'{"ACTION": ^{wid-2}}||'
            f'{("CHARGE" if requests["Full_Charge"] else "NORMAL"): ^{wid-1}}|'
            f'{("CHARGE" if requests["Force_Charge"] else "NORMAL"): ^{wid-1}}|'
            f'{("ENABLE" if requests["Charge_Enable"] else "STOP"): ^{wid-1}}|'
            f'{("ENABLE" if requests["Discharge_Enable"] else "STOP"): ^{wid-1}}|\n'
        )
        screen+=f'\n{"":-^{wid*5}}'
        print(screen)


    def close(self):
        bus.shutdown()
        print('Ending')
    



if __name__ == '__main__':
    try:
        subprocess.run("sudo ip link set can0 down", shell=True, check=True) # Set CAN0 down
        subprocess.run("sudo ip link set can0 up type can bitrate 500000", shell=True, check=True) # Set CAN0 up
        bus = can.interface.Bus(interface='socketcan', channel='can0', bitrate=500000)
        filters=[
            # {"can_id": 0x320, "can_mask": 0x1FFFFF00, "extended": True},
            # {"can_id": 0x322, "can_mask": 0x1FFFFFFF, "extended": True},
            {"can_id": 0x351, "can_mask": 0x7FF, "extended": False}, # Limits
            {"can_id": 0x355, "can_mask": 0x7FF, "extended": False}, # States
            {"can_id": 0x356, "can_mask": 0x7FF, "extended": False}, # Values
            {"can_id": 0x359, "can_mask": 0x7FF, "extended": False}, # Flags
            {"can_id": 0x35C, "can_mask": 0x7FF, "extended": False}, # Requests
            # {"can_id": 0x9691FFFF, "can_mask": 0x1F000000, "extended": True},
            # {"can_id": 0x96900001, "can_mask": 0x1FFFFFFF, "extended": True},
            # {"can_id": 0x96910001, "can_mask": 0x1FFFFFFF, "extended": True},
            # {"can_id": 0x96920001, "can_mask": 0x1FFFFFFF, "extended": True},
            # {"can_id": 0x96930001, "can_mask": 0x1FFFFFFF, "extended": True},
            # {"can_id": 0x96940001, "can_mask": 0x1FFFFFFF, "extended": True},
            # {"can_id": 0x96950001, "can_mask": 0x1FFFFFFF, "extended": True},
            # {"can_id": 0x96960001, "can_mask": 0x1FFFFFFF, "extended": True},
            # {"can_id": 0x96970001, "can_mask": 0x1FFFFFFF, "extended": True},
            # {"can_id": 0x96980001, "can_mask": 0x1FFFFFFF, "extended": True},
            # {"can_id": 0x96990001, "can_mask": 0x1FFFFFFF, "extended": True},
            # {"can_id": 0x969a0001, "can_mask": 0x1FFFFFFF, "extended": True},
            # {"can_id": 0x969b0001, "can_mask": 0x1FFFFFFF, "extended": True},
            # {"can_id": 0x969c0001, "can_mask": 0x1FFFFFFF, "extended": True},
            # {"can_id": 0x969d0001, "can_mask": 0x1FFFFFFF, "extended": True},
            # {"can_id": 0x969e0001, "can_mask": 0x1FFFFFFF, "extended": True},
            # {"can_id": 0x969f0001, "can_mask": 0x1FFFFFFF, "extended": True},
            # {"can_id": 0x96a00001, "can_mask": 0x1FFFFFFF, "extended": True},
            # {"can_id": 0x96a10001, "can_mask": 0x1FFFFFFF, "extended": True},
        ]
        bus.set_filters(filters)
        dbc=cantools.database.load_file('SG48200T.dbc')
        dev=Device(db=dbc,debug=True)
        notifier=can.Notifier(bus,[dev])
    except:
        try:
            bus.shutdown()
            dev.close()
            notifier.stop()
        finally:
            raise Exception('CAN or DBC error')
    time.sleep(2)
    start=time.time()
    while(True):
        try:
            dev.screen()
            # dev.dump()
            time.sleep(1)
        except KeyboardInterrupt:
            print('\nClosing')
            break
        except Exception as e:
            print(e)
            break
    notifier.stop()
    dev.close()


    