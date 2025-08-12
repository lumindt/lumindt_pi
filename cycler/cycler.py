from transitions import Machine, MachineError
import threading
import time
import csv
import board as board
from utils.sensors import ADS1115
from utils.omega import FMA1820A
from utils.FSM import FSM

if __name__ == '__main__':

    file=f'test{time.strftime("%Y%m%d_%H%M%S")}.csv'
    
    cycler=FSM()
    
    acc_in = 0.0
    acc_out = 0.0

    SLPM2GPS = 1.50

    ads0 = ADS1115(addr=0x48)
    ads1 = ADS1115(addr=0x49)
    FM = FMA1820A(addr=0x4B)

    def _accumulator():
        global acc_in, acc_out
        while True:
            t_start=time.time()
            time.sleep(0.0001)
            f_i=FM.flow(0) * SLPM2GPS
            f_o=FM.flow(1) * SLPM2GPS
            acc_in+=f_i*(time.time()-t_start)
            acc_out+=f_o*(time.time()-t_start)   



    _flow_thread=threading.Thread(target=_accumulator,daemon=True)
    _thread_lock=threading.Lock()
    _flow_thread.start()
  
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
        time.sleep(1)

        e=None
        init=time.time()

        while True:
            try:
                prev=time.time()
                state=cycler.state

                tc1=ads0.temperature(0)
                pti=ads0.pressure(2)
                pto=ads1.pressure(2)

                with _thread_lock:
                    fi_val=acc_in
                    fo_val=acc_out

                cycle = 1

                string=(
                    '--------------------\n'
                    f'Time:     {prev-init:0.2f}\n'
                    f'State:    {state}\n'
                    f'Cycle:    {cycle}\n'
                    f'Temp:     {tc1:0.2f} C\n'
                    f'FMI:      {FM.flow(1)} L\n'
                    f'FMO:      {FM.flow(0)} L\n'
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
                    cmd=int(input(
                        '\n\nInput Options:\n'
                        '------------------\n'
                        '0 -> Standby\n'
                        '1 -> Resume\n'
                        '2 -> Start Cycling\n'
                        '3 -> Manual Absorb\n'
                        '4 -> Manual Desorb\n'
                        '5 -> LEAK TEST (VALVES OPEN)\n'
                        'Press ENTER to end script\n'
                    ))
                    if cmd==0: cycler.stop()
                    elif cmd==2: 
                        absorb_time = 10
                        hold_time = 10
                        desorb_time = 10
                        no_cycles = input('Number of cycles: ')
                        current_cycle = 0
                        try:
                            for i in range(0, int(no_cycles)):
                                print(cycle)
                                cycler.fill()
                                time.sleep(10)
                                cycler.stop()
                                time.sleep(10)
                                cycler.empty()
                                time.sleep(10) # cycle reset time
                        except Exception as ex:
                            print(f"Cycle interrupted due to error: {ex}")
                            break
                    elif cmd==3: cycler.fill()
                    elif cmd==4: cycler.empty()
                    elif cmd==5:
                           cycler.svi.on()
                           time.sleep(1)
                           cycler.svo.on()
                    else: continue
                except:
                    print('Exiting...')
                    break
            except Exception as e:
                print(e)
                break

    cycler.stop()
    time.sleep(1)
    cycler.end()
