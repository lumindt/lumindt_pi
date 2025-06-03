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

    # Shortcut methods like R1on(), R2off(), etc.
    for relay in self.relay_pins:
        setattr(self, f"{relay}on", lambda r=relay: self.on(r))
        setattr(self, f"{relay}off", lambda r=relay: self.off(r))

    # Shortcut for all_off() so it's consistent with naming
    setattr(self, "alloff", self.all_off)

def main():
    board = RelayBoard()
    board.run_cli()

if __name__ == '__main__':
    main()
