from transitions import Machine, MachineError
import threading
import time
import csv
import board as board
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.sensors import ADS1115
from utils.omega import OmegaFM 
from utils.relay import RelayBoard, RelayControl

def csv_check(name):
    if os.path.exists(name+'.csv'):
        print('File already exists!')
        return csv_check(name+'_c')
    else:
        return name
    
class CyclerFSM:

    SLPM2GPS = 1.50  # ratio of [g/s] / [slpm] for hydrogen

    def __init__(self):
        transitions = [
            {'trigger': 'stop', 'source': '*', 'dest': 'standby'},
            {'trigger': 'end', 'source': 'standby', 'dest': 'clean'},
            {'trigger': 'fill', 'source': ['standby', 'desorb'], 'dest': 'absorb'},
            {'trigger': 'empty', 'source': ['standby', 'absorb'], 'dest': 'desorb'},
        ]

        self.machine = Machine(
            model=self,
            states=[
            'standby',
            'absorb',
            'desorb',
            'clean',
            ],
            transitions=transitions,
            initial='standby'
        )

        self._timer = None

        ads0 = ADS1115(addr=0x48)
        ads1 = ADS1115(addr=0x49)

        self.FM = OmegaFM(addr=0x4B)
        self.FMI = self.FM.flow(pinout=0) 
        self.FMO = self.FM.flow(pinout=1)

        self.TC1 = ads0.temperature(1)
        self.PTI = ads0.pressure()
        self.PTO = ads1.pressure()

        relay_board = RelayBoard()

        self.svi = RelayControl(relay_board=relay_board,relay='R1')
        self.svo = RelayControl(relay_board=relay_board,relay='R2')


        self._flow_thread=threading.Thread(target=self._accumulator,daemon=True)
        self._flow_in_flag=threading.Event()
        self._flow_out_flag=threading.Event()
        self._flow_thread.start()

        self._thread_lock=threading.Lock()
        self.acc_in=0
        self.acc_out=0

    def _accumulator(self):
        while True:
            t_start=time.time()
            time.sleep(0.0001)

            f_i=round(self.FMI) * self.SLPM2GPS
            f_o=round(self.FMO) * self.SLPM2GPS

            with self._thread_lock:
                self.acc_in+=f_i*(time.time()-t_start)
                self.acc_out+=f_o*(time.time()-t_start)   
    
    def on_enter_standby(self):
        self.flow_none()
        self.clear_timer()

    def on_enter_absorb(self):
        self.flow_in()

    def on_enter_desorb(self):
        self.flow_out()

    def flow_in(self):
        time.sleep(0.2)
        self.svo.off()
        time.sleep(2)
        self.svi.on()

    def flow_out(self):
        time.sleep(0.2)
        self.svi.off()
        time.sleep(2)
        self.svo.on()

    def flow_none(self):
        time.sleep(0.2)
        self.svo.off()
        self.svi.off()

    def fill_timer(self):
        self._timer=threading.Timer(5,self.auto_pause)
        self._timer.start()

    def pause_timer(self):
        self._timer=threading.Timer(2,self.auto_empty)
        self._timer.start()

    def empty_timer(self):
        self._timer=threading.Timer(5,self.auto_fill)
        self._timer.start()

    def clear_timer(self):
        if self._timer:
            self._timer.cancel()
            self._timer=None


if __name__ == '__main__':

    file='test'
    file=csv_check(file)
    file=file+'.csv'

    with open(file, 'w', newline='') as f:
        writer=csv.writer(f)
        writer.writerow([
            'Time',
            'State',
            'TC1',
            'PTI',
            'PTO',
            'TMI',
            'TMO'
        ])
        cycler=CyclerFSM()
        time.sleep(1)

        e=None
        init=time.time()

        while True:
            try:
                prev=time.time()
                state=cycler.state

                tc1=cycler.TC1
                pti=cycler.PTI
                pto=cycler.PTO

                with cycler._thread_lock:
                    fi_val=cycler.acc_in
                    fo_val=cycler.acc_out

                string=(
                    '--------------------\n'
                    f'Time:     {prev-init:0.2f}\n'
                    f'State:    {state}\n'
                    # f'Tank:     {tank_val}\n'
                    f'Temp:     {tc1:0.2f} C\n'
                    f'PTI:      {pti:0.2f} bar\n'
                    f'PTO:      {pto:0.2f} bar\n'
                    f'TMI:      {fi_val:0.6f} g \n'
                    f'TMO:      {fo_val:0.6f} g \n'
                    f'EXP:      {e}\n'
                    '--------------------\n'
                )

                print(string)
                writer.writerow([
                    prev-init,
                    state,
                    tc1,
                    pti,
                    pto,
                    fi_val,
                    fo_val,
                ])
                
                while time.time()-prev<1: pass
            except KeyboardInterrupt:
                try:
                    cmd=input(
                        '\n\nInput Options:\n'
                        '------------------\n'
                        '0 -> Standby\n'
                        '1 -> Resume\n'
                        # '2 -> Start Cycling\n'
                        '3 -> Manual Absorb\n'
                        '4 -> Manual Desorb\n'
                        '5 -> Test Pressure\n'
                        '6 -> EXIT\n\n'
                    )
                    if cmd=='0': cycler.stop()
                    # elif cmd=='2': cycler.auto_fill()
                    elif cmd=='3':
                            cycler.fill()
                    elif cmd=='4': cycler.empty()
                    elif cmd=='5':
                        ptest=float(input('\nnew pressure value\n'))
                        cycler._tank_pressure=ptest
                    elif cmd=='6':
                        print('Exiting...')
                        break
                    else: pass
                except MachineError as m:
                    print(m)
            except Exception as e:
                print(e)
                break

    cycler.stop()
    time.sleep(1)
    cycler.end()
