import RPi.GPIO as GPIO

class RelayBoard:
    def __init__(self):
        # Relay to GPIO pin mapping
        self.relay_pins = {
            'R1': 17,  # V1
            'R2': 27,  # V1
            'R3': 22,  # V2
            'R4': 23   # V2
        }
        # Voltage groups
        self.v1_relays = ['R1', 'R2']
        self.v2_relays = ['R3', 'R4']

        GPIO.setmode(GPIO.BCM)

        GPIO.setwarnings(False)

        for pin in self.relay_pins.values():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

        self.relay_objects = {
            relay: RelayControl(self, relay)
            for relay in self.relay_pins.keys()
        }

class RelayControl:
    def __init__(self, relay_board, relay: str):
        self.relay_board = relay_board
        self.relay = relay

        if relay not in self.relay_board.relay_pins:
            raise ValueError("Invalid relay name (expected R1–R4)")

        self.pin = self.relay_board.relay_pins[relay]

        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)

    def __enter__(self):
        return self
        
    def __exit__(self):
        GPIO.output(self.pin, GPIO.LOW)
        GPIO.cleanup(self.pin)



    def on(self):
        if self.relay not in self.relay_board.relay_pins:
            raise ValueError("Invalid relay name (expected R1–R4)")
        GPIO.output(self.relay_board.relay_pins[self.relay], GPIO.HIGH)

    def off(self):
        if self.relay not in self.relay_board.relay_pins:
            raise ValueError("Invalid relay name (expected R1–R4)")
        GPIO.output(self.relay_board.relay_pins[self.relay], GPIO.LOW)



    def toggle(self, relay: str):
        if relay not in self.relay_board.relay_pins:
            raise ValueError("Invalid relay name (expected R1–R4)")
        pin = self.relay_board.relay_pins[relay]

        GPIO.output(pin, not GPIO.input(pin))


    def status(self):
        return {
            relay: GPIO.input(pin)
            for relay, pin in self.relay_board.relay_pins.items()
        }


    def all_off(self):
        for pin in self.relay_board.relay_pins.values():
            GPIO.output(pin, GPIO.LOW)

    def cleanup(self):
        GPIO.cleanup()


    def v1_on(self):
        for relay in self.relay_board.v1_relays:
            self.on(relay)

    def v1_off(self):
        for relay in self.relay_board.v1_relays:
            self.off(relay)

    def v2_on(self):
        for relay in self.relay_board.v2_relays:
            self.on(relay)

    def v2_off(self):
        for relay in self.relay_board.v2_relays:
            self.off(relay)

    def run_cli(self):
        print("Relay Control CLI (type 'V1 ON', 'R2 OFF', etc.)")
        try:
            while True:
                cmd = input("Command: ").strip().upper()
                if cmd == 'Q':
                    break

                if cmd in ['V1 ON', 'V1 OFF']:
                    getattr(self, f"v1_{cmd.split()[1].lower()}")()


                elif cmd in ['V2 ON', 'V2 OFF']:
                    getattr(self, f"v2_{cmd.split()[1].lower()}")()


                else:
                    parts = cmd.split()
                    if len(parts) == 2 and parts[0] in self.relay_pins and parts[1] in ['ON', 'OFF']:
                        getattr(self, parts[1].lower())(parts[0])

                    else:
                        print("Invalid command.")


        except KeyboardInterrupt:
            pass


        finally:
            self.all_off()
            self.cleanup()

if __name__ == '__main__':
    relay_board = RelayBoard()
    relay_control = RelayControl(relay_board, 'R1')
    
    try:
        relay_control.run_cli()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        relay_control.cleanup()




