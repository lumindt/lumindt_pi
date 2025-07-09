import lgpio
import time

class RelayBoard:
    def __init__(self):
        # Relay to GPIO pin mapping
        self.relay_pins = {
            'R1': 17,
            'R2': 27,
            'R3': 22,
            'R4': 23
        }

        # Voltage groups
        self.v1_relays = ['R1', 'R2']
        self.v2_relays = ['R3', 'R4']

        # Open GPIO chip
        self.handle = lgpio.gpiochip_open(0)

        # Set up relay pins as outputs and default to LOW
        for pin in self.relay_pins.values():
            lgpio.gpio_claim_output(self.handle, pin, 0)

        self.relay_objects = {
            relay: RelayControl(self, relay)
            for relay in self.relay_pins.keys()
        }

    def cleanup(self):
        for pin in self.relay_pins.values():
            lgpio.gpio_write(self.handle, pin, 0)
        lgpio.gpiochip_close(self.handle)

class RelayControl:
    def __init__(self, relay_board, relay: str):
        self.relay_board = relay_board
        self.relay = relay

        if relay not in self.relay_board.relay_pins:
            raise ValueError("Invalid relay name (expected R1–R4)")

        self.pin = self.relay_board.relay_pins[relay]
        self.handle = self.relay_board.handle
        lgpio.gpio_write(self.handle, self.pin, 0)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.off()

    def on(self):
        lgpio.gpio_write(self.handle, self.pin, 1)

    def off(self):
        lgpio.gpio_write(self.handle, self.pin, 0)

    def toggle(self, relay=None):
        if relay:
            return self.relay_board.relay_objects[relay].toggle()
        state = lgpio.gpio_read(self.handle, self.pin)
        lgpio.gpio_write(self.handle, self.pin, 1 - state)

    def status(self):
        return {
            relay: lgpio.gpio_read(self.handle, pin)
            for relay, pin in self.relay_board.relay_pins.items()
        }

    def all_off(self):
        for pin in self.relay_board.relay_pins.values():
            lgpio.gpio_write(self.handle, pin, 0)

    def v1_on(self):
        for relay in self.relay_board.v1_relays:
            self.relay_board.relay_objects[relay].on()

    def v1_off(self):
        for relay in self.relay_board.v1_relays:
            self.relay_board.relay_objects[relay].off()

    def v2_on(self):
        for relay in self.relay_board.v2_relays:
            self.relay_board.relay_objects[relay].on()

    def v2_off(self):
        for relay in self.relay_board.v2_relays:
            self.relay_board.relay_objects[relay].off()

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
                    if len(parts) == 2 and parts[0] in self.relay_board.relay_pins and parts[1] in ['ON', 'OFF']:
                        getattr(self.relay_board.relay_objects[parts[0]], parts[1].lower())()
                    else:
                        print("Invalid command.")
        except KeyboardInterrupt:
            pass
        finally:
            self.all_off()
            self.relay_board.cleanup()

if __name__ == '__main__':
    relay_board = RelayBoard()
    relay_control = relay_board.relay_objects['R1']
    try:
        relay_control.run_cli()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        relay_control.all_off()
        relay_board.cleanup()
