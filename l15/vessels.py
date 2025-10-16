import gpiozero
import busio
import board
import time
import csv
from utilities.sensors import ADS1115
from utilities.sensors_v2 import LTC2983

# === NEW: FC pressure safety config ===
FC_MIN_BAR = 3.0          # close *out* valves if FC pressure stays below this
FC_HYST_BAR = 0.3         # reopen only after FC >= FC_MIN_BAR + FC_HYST_BAR
FC_LOW_SAMPLES = 3        # require this many consecutive low samples before closing
LOG_PERIOD_S = 2.0
# ======================================

# === NEW: state for debounce/hysteresis ===
_fc_low_count = 0
_fc_cutoff_active = False
# ==========================================

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
LTC=LTC2983(spi)

HES_in=gpiozero.OutputDevice(pin=17)
HES_out=gpiozero.OutputDevice(pin=27)
C5_in=gpiozero.OutputDevice(pin=22)
C5_out=gpiozero.OutputDevice(pin=23)

file='outputs/idgaf.csv'
with open(file, 'w', newline='') as f:
    writer=csv.writer(f)
    writer.writerow([
        'Time (s)',
        'HES in',
        'HES out',
        'C5 in',
        'C5 out',
        'HES Vessel Pressure (barG)',
        'FC Pressure (barG)',
        'C5 Vessel Pressure (barG)',
        'EL Pressure (barG)',
        'some Temp (C)'
    ])
    t_start=time.time()
    next_tick = t_start
    while True:
        try:
            now = time.time()
            if now < next_tick:
                time.sleep(next_tick - now)
                now = time.time()
            next_tick += LOG_PERIOD_S

            t_now=now-t_start
            HES_in_status=HES_in.value
            HES_out_status=HES_out.value
            C5_in_status=C5_in.value
            C5_out_status=C5_out.value
            p_v1=LTC.pres(11)
            p_v2=LTC.pres(14)
            p_FC=LTC.pres(2)
            p_EL=LTC.pres(13)
            t_V1 = LTC.temp(1)

                        # === NEW: Debounce + hysteresis safety on FC pressure ===
            # Close HES_out / C5_out only if FC stays < FC_MIN_BAR for FC_LOW_SAMPLES in a row.
            # Once closed by this safety, don't allow reopening until FC >= FC_MIN_BAR + FC_HYST_BAR.
            if p_FC is not None:
                if not _fc_cutoff_active:
                    if p_FC < FC_MIN_BAR:
                        _fc_low_count += 1
                        if _fc_low_count >= FC_LOW_SAMPLES:
                            # close drain valves
                            if HES_out.value:
                                HES_out.off()
                            if C5_out.value:
                                C5_out.off()
                            _fc_cutoff_active = True
                    else:
                        _fc_low_count = 0
                else:
                    # currently in cutoff; wait for hysteresis to clear
                    if p_FC >= (FC_MIN_BAR + FC_HYST_BAR):
                        _fc_cutoff_active = False
                        _fc_low_count = 0

                # refresh statuses after any changes
                HES_out_status = HES_out.value
                C5_out_status  = C5_out.value
            # =======================================================


            writer.writerow([
                t_now-t_start,
                HES_in_status,
                HES_out_status,
                C5_in_status,
                C5_out_status,
                p_v1,
                p_v2,
                p_FC,
                p_EL
            ])

            string=(
                f'{"":-^30}\n'
                f'Time:         {t_now:0.2f}\n'
                f'HES in:           {HES_in_status}\n'
                f'HES out:           {HES_out_status}\n'
                f'C5_in:           {C5_in_status}\n'
                f'C5_out:           {C5_out_status}\n'
                f'V1 Pres:  {p_v1:0.2f} barG\n'
                f'V2 Pres:  {p_v2:0.2f} barG\n'
                f'FC Pres:    {p_FC:0.2f} barG\n'
                f'EL Pres:    {p_EL:0.2f} barG\n'
                f'V1 Temp 1:    {t_V1:0.2f} C\n'
                )
            print(string)
            while time.time()-t_now-t_start<1:
                pass
        except KeyboardInterrupt:
            cmdstring=(
                f'\n\n0 -> Close\n'
                f'1 -> HES Fill\n'
                f'2 -> HES Drain\n'
                f'3 -> C5 Fill\n'
                f'4 -> C5 Drain\n'
                f'5 -> Continue\n'
                f'enter anything else to quit\n'
            )
            print(cmdstring)
            cmd=input('Command: ')
            if cmd=='0':
                print('Closing')
                HES_in.off()
                HES_out.off()
                C5_out.off()
                C5_in.off()
            elif cmd=='1':
                print('HES Absorb')
                time.sleep(0.2)
                HES_in.on()
                HES_out.off()
            elif cmd=='2':
                print('HES Desorb')
                time.sleep(0.2)
                HES_in.off()
                HES_out.on()
            elif cmd=='3':
                print('C5 Absorb')
                time.sleep(0.2)
                C5_in.on()
                C5_out.off()
            elif cmd=='4':
                print('C5 Desorb')
                time.sleep(0.2)
                C5_in.off()
                C5_out.on()
            elif cmd=='5':
                print('Continuing')
                pass
            else:
                break
HES_in.close()
HES_out.close()
C5_in.close()
C5_out.close()
