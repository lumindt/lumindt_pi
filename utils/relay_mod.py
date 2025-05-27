import RPi.GPIO as GPIO
import time

class RelayBoard:
    def __init__(self):
        # Relay to GPIO pin mapping (BCM mode)
        self.relay_pins = {
            'R1': 17,  # R1
            'R2': 27,  # R2
            'R3': 22,  # R3
            'R4': 23   # R4
        }

        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        for pin in self.relay_pins.values():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)  # Start with all relays OFF

    def on(self, relay: str):
        if relay not in self.relay_pins:
            raise ValueError("Invalid relay name (expected R1–R4)")
        GPIO.output(self.relay_pins[relay], GPIO.HIGH)

    def off(self, relay: str):
        if relay not in self.relay_pins:
            raise ValueError("Invalid relay name (expected R1–R4)")
        GPIO.output(self.relay_pins[relay], GPIO.LOW)

    def toggle(self, relay: str):
        if relay not in self.relay_pins:
            raise ValueError("Invalid relay name (expected R1–R4)")
        pin = self.relay_pins[relay]
        GPIO.output(pin, not GPIO.input(pin))

    def status(self):
        return {
            relay: GPIO.input(pin)
            for relay, pin in self.relay_pins.items()
        }

    def all_off(self):
        for pin in self.relay_pins.values():
            GPIO.output(pin, GPIO.LOW)

    def cleanup(self):
        GPIO.cleanup()

    def run_cli(self):
        print("Relay Control CLI: enter relay name (R1–R4) and ON/OFF/TGL. Type Q to quit.")
        try:
            while True:
                cmd = input("Command (e.g. 'R1 ON'): ").strip().upper()
                if cmd == 'Q':
                    break
                parts = cmd.split()
                if len(parts) != 2:
                    print("Invalid command. Format: <relay> <ON/OFF/TGL>")
                    continue
                relay_name = parts[0]
                action = parts[1]

                if action == 'ON':
                    self.on(relay_name)
                elif action == 'OFF':
                    self.off(relay_name)
                elif action == 'TGL':
                    self.toggle(relay_name)
                else:
                    print("Unknown action. Use ON, OFF, or TGL.")
                print("Relay states:", self.status())

        except KeyboardInterrupt:
            pass
        finally:
            self.all_off()
            self.cleanup()

if __name__ == '__main__':
    board = RelayBoard()
    board.run_cli()
