import serial
import time

class MP710256:

    STATUS_FLAGS = [
        "CV MODE",      # Bit 0
        "OUTPUT",       # Bit 1
        "PRIORITY CC",  # Bit 2
        "NONE",         # Bit 3
        "BUZZER",       # Bit 4
        "LOCK",         # Bit 5
        "OVP",          # Bit 6
        "OCP",          # Bit 7
    ]

    def __init__(self, port, id):
        self.ser = serial.Serial(
            port=port,
            baudrate=115200,
            bytesize=serial.EIGHTBITS,  # 8 data bits (default)
            parity=serial.PARITY_NONE,   # No parity (default)
            stopbits=serial.STOPBITS_ONE, # 1 stop bit (default)
            timeout=1
        )
        self.id = id
        time.sleep(2)  # Wait for the serial connection to initialize

    def command(self, register, value = None):
        if value is not None:
            command = f'{register}{self.id:02d}:{value}\n'
            self.ser.write(command.encode())
        else:
            command = f'{register}{self.id:02d}?\n'
            self.ser.write(command.encode())
            return self.ser.readline().strip()

    @property
    def VOUT(self):
        return float(self.command(register = 'VOUT').decode())
    @VOUT.setter
    def VOUT(self, voltage):
        self.command(register = 'VOUT', value = round(voltage,3))

    @property
    def IOUT(self):
        return float(self.command(register = 'IOUT').decode())
    @IOUT.setter
    def IOUT(self, current):
        self.command(register = 'IOUT', value = round(current,3))

    @property
    def ISET(self):
        return float(self.command(register = 'ISET').decode())
    @ISET.setter
    def ISET(self, current):
        self.command(register = 'ISET', value = round(current,3))

    @property
    def VSET(self):
        return float(self.command(register = 'VSET').decode())
    @VSET.setter
    def VSET(self, voltage):
        self.command(register = 'VSET', value = round(voltage,3))

    @property
    def OUT(self):
        return bool(int(self.command(register = 'OUT')))
    @OUT.setter
    def OUT(self, state):
        self.command(register = 'OUT', value = 1 if state else 0)

    @property
    def STATUS(self):
        value = int.from_bytes(self.command(register = 'STATUS'), byteorder='big')
        return {
            name: bool(value & (1 << i)) 
            for i, name in enumerate(self.STATUS_FLAGS)
        }
    
    def close(self):
        self.OUT = False  # Ensure output is turned off before closing
        self.ser.close()

if __name__ == "__main__":
    psu = MP710256(port = '/dev/ttyACM0', id = 1)
    while True:
        try:
            status = psu.STATUS
            indicators = ['CV MODE', 'OUTPUT']
            print_status = {key: status[key] for key in indicators}
            print_string = (
                f'{"-"*30}\n'
                f'STATUS: {print_status}\n'
                f'VSET: {psu.VSET} V | VOUT: {psu.VOUT} V\n'
                f'ISET: {psu.ISET} A | IOUT: {psu.IOUT} A\n'
            )
            print(print_string)
            time.sleep(1)
        except Exception as e:
            print(f"Error reading PSU status: {e}")
            break
        except KeyboardInterrupt:
            try:
                cmd = int(input(
                    "\n"
                    "Set On:        0\n"
                    "Set Voltage:   1\n"
                    "Set Current:   2\n"
                    "Resume:        3+\n"
                    "Exit:          Enter\n"
                ))
                if cmd == "0":
                    on_off = input("Enter 1 to turn ON or 0 to turn OFF: ")
                    psu.OUT = True if on_off == "1" else False
                elif cmd == "1":
                    voltage = float(input("Enter voltage (V): "))
                    psu.VSET = min(30, max(0, voltage))
                elif cmd == "2":
                    current = float(input("Enter current (A): "))
                    psu.ISET = min(30, max(0, current))
                else:
                    print("Resuming...")
            except:
                print("\nExiting...")
                break
    psu.close()