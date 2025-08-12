from transitions import Machine, MachineError
import threading
import time
import csv
import board as board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import gpiozero
import os

# raise Exception('fix all the flow meter shit before running')

def csv_check(name):
    if os.path.exists(name+'.csv'):
        print('File already exists!')
        return csv_check(name+'_c')
    else:
        return name

class FSM:

    SLPM2GPS=1.50 # ratio of [g/s] / [slpm] for hydrogen

    def __init__(self):
        self.machine=Machine(
            model=self,
            states=[
                'standby',
                'absorb',
                'desorb',
                'auto_absorb',
                'auto_wait',
                'auto_desorb',
                'clean'
            ],
            initial='standby')

        self.machine.add_transition('stop','*','standby')
        self.machine.add_transition('end','standby','clean',after='_cleanup')
        self.machine.add_transition('fill',['standby','desorb'],'absorb',conditions='tank_check')
        self.machine.add_transition('empty',['standby','absorb'],'desorb')
        self.machine.add_transition('auto_fill',['standby','auto_desorb'],'auto_absorb',conditions='tank_check',before='clear_timer',after='fill_timer')
        self.machine.add_transition('auto_pause','auto_absorb','auto_wait',before='clear_timer',after='pause_timer')
        self.machine.add_transition('auto_empty','auto_wait','auto_desorb',before='clear_timer',after='empty_timer')

        self._timer=None

        i2c = busio.I2C(board.SCL, board.SDA)
        ads0 = ADS.ADS1115(i2c)
        ads1 = ADS.ADS1115(i2c,address=0x49)
        ads2 = ADS.ADS1115(i2c,address=0x4B)
        ads2.gain=2/3
        self.c00 = AnalogIn(ads0, ADS.P0)
        self.c01 = AnalogIn(ads0, ADS.P1)
        self.c02 = AnalogIn(ads0, ADS.P2)
        self.c03 = AnalogIn(ads0, ADS.P3)
        self.c10 = AnalogIn(ads1, ADS.P0)
        self.c11 = AnalogIn(ads1, ADS.P1)
        self.c12 = AnalogIn(ads1, ADS.P2)
        self.c13 = AnalogIn(ads1, ADS.P3)
        self.c20 = AnalogIn(ads2, ADS.P0)
        self.c21 = AnalogIn(ads2, ADS.P1)

        self.svi = gpiozero.OutputDevice(22)
        self.svo = gpiozero.OutputDevice(24)

        self._tank_pressure=0
        self._tank_flag=threading.Event()
        self._tank_thread=threading.Thread(target=self._tank_watcher,daemon=True)
        self._tank_thread.start()

        self._flow_thread=threading.Thread(target=self._accumulator,daemon=True)
        self._flow_in_flag=threading.Event()
        self._flow_out_flag=threading.Event()
        self._flow_thread.start()

        self._thread_lock=threading.Lock()
        self.acc_in=0
        self.acc_out=0

    @property
    def TC1(self):
        return (self.c00.voltage)/0.005
    
    @property
    def PTI(self):
        return (self.c12.voltage/165-0.004)/0.016*(68.95)
    
    @property
    def PTO(self):
        return (self.c02.voltage/165-0.004)/0.016*(68.95)

    def _accumulator(self):
        while True:
            t_start=time.time()
            time.sleep(0.0001)
            if 'wait' in self.state:
                self._flow_in_flag.clear()
                self._flow_out_flag.clear()
            if self.state=='clean':
                break
            v_i=self.c21.voltage
            v_o=self.c20.voltage
            if v_i>=5: self._flow_in_flag.set()
            if v_o>=5: self._flow_out_flag.set()
            f_i=round(v_i/5*10*1.0106,1)*FSM.SLPM2GPS
            f_o=round(v_o/5*10*1.0106,1)*FSM.SLPM2GPS
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

    def on_enter_auto_wait(self):
        self.flow_none()

    def on_enter_auto_absorb(self):
        self.flow_in()
        with self._thread_lock:
            self.acc_in=0
            self.acc_out=0

    def on_enter_auto_desorb(self):
        self.flow_out()


    def flow_in(self):
        time.sleep(0.2)
        self.svo.off()
        time.sleep(0.5)
        self.svi.on()

    def flow_out(self):
        time.sleep(0.2)
        self.svi.off()
        time.sleep(0.5)
        self.svo.on()

    def flow_none(self):
        time.sleep(0.2)
        self.svo.off()
        self.svi.off()


    def _tank_watcher(self):
        while self.state!='clean':
            if self._tank_pressure<40:
                self._tank_flag.set()
                if self.state!='standby':
                    print('Tank Low')
                    time.sleep(0.2)
                    self.stop()
            else:
                self._tank_flag.clear()
            time.sleep(0.2)

    def tank_check(self):
        if self._tank_flag.is_set(): print('Tank Still Low')
        return not self._tank_flag.is_set()

    def _cleanup(self):
        self._tank_thread.join()
        self._flow_thread.join()
        self.svi.close()
        self.svo.close()
        print('\n\nFSM ended')
        
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


file='test'
# file=csv_check(file)
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
    cycler=FSM()
    time.sleep(1)
    e=None
    init=time.time()
    while True:
        try:
            prev=time.time()
            state=cycler.state
            tank_val='Low' if cycler._tank_flag.is_set() else 'Good'
            tc1=cycler.TC1
            pti=cycler.PTI
            pto=cycler.PTO
            with cycler._thread_lock:
                ai_val=cycler.acc_in
                ao_val=cycler.acc_out
            fi_val='Overflow' if cycler._flow_in_flag.is_set() else None
            fo_val='Overflow' if cycler._flow_out_flag.is_set() else None
            string=(
                '--------------------\n'
                f'Time:     {prev-init:0.2f}\n'
                f'State:    {state}\n'
                f'Tank:     {tank_val}\n'
                f'Temp:     {tc1:0.2f} C\n'
                f'PTI:      {pti:0.2f} bar\n'
                f'PTO:      {pto:0.2f} bar\n'
                f'TMI:      {ai_val:0.6f} g {fi_val}\n'
                f'TMO:      {ao_val:0.6f} g {fo_val}\n'
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
                ai_val,
                ao_val,
            ])
            
            while time.time()-prev<1: pass
        except KeyboardInterrupt:
            try:
                cmd=float(input(
                    '\n\nInput Options:\n'
                    '------------------\n'
                    '0 -> Standby\n'
                    '1 -> Resume\n'
                    '2 -> Start Cycling\n'
                    '3 -> Manual Absorb\n'
                    '4 -> Manual Desorb\n'
                    '5 -> Test Pressure\n\n'
                ))
                if cmd==0: cycler.stop()
                elif cmd==2: cycler.auto_fill()
                elif cmd==3: cycler.fill()
                elif cmd==4: cycler.empty()
                elif cmd==5:
                    ptest=float(input('\nnew pressure value\n'))
                    cycler._tank_pressure=ptest
                else: pass
            except MachineError as m:
                print(m)
            except:
                print('Invalid Input')
                break
        except Exception as e:
            print(e)
            break

cycler.stop()
time.sleep(1)
cycler.end()


