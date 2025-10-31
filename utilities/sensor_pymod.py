import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn


def map_value(x, xmin, xmax, ymin, ymax):
    return (x - xmin) * (ymax - ymin) / (xmax - xmin) + ymin


class ADS1115:
    def __init__(self, addr=0x48):
        bus = busio.I2C(board.SCL, board.SDA)
        self.ads = ADS.ADS1115(bus, address=addr)

        self.rates = [8, 16, 32, 64, 128, 250, 475, 860]
        self.gains = [2/3, 1, 2, 4, 8, 16]

        self._gain = 2/3
        self._data_rate = 64
        self.initialized = True

        self._write_config()

        self.channels = {
            0: AnalogIn(self.ads, ADS.P0),
            1: AnalogIn(self.ads, ADS.P1),
            2: AnalogIn(self.ads, ADS.P2),
            3: AnalogIn(self.ads, ADS.P3)
        }

    def _write_config(self):
        self.ads.gain = self._gain
        self.ads.data_rate = self._data_rate

    @property
    def data_rate(self):
        return self._data_rate

    @data_rate.setter
    def data_rate(self, rate):
        if rate not in self.rates:
            raise ValueError(f"Data rate must be one of: {self.rates}")
        self._data_rate = rate
        if self.initialized:
            self._write_config()

    @property
    def gain(self):
        return self._gain

    @gain.setter
    def gain(self, gain):
        if gain not in self.gains:
            raise ValueError(f"Gain must be one of: {self.gains}")
        self._gain = gain
        if self.initialized:
            self._write_config()

    def read_voltage(self, pin):
        return self.channels[pin].voltage

    def pressure(self, pin=0, res=165, max_bar=68.95):
        v = self.read_voltage(pin)
        return map_value(v / res, 0.004, 0.020, 0.0, max_bar)

    def temperature(self, pin=0, offset=0):
        v = self.read_voltage(pin)
        return (v - offset) / 0.005


class SensorBoard:
    def __init__(self):
        self.adcs = {
            0x48: ADS1115(0x48),
            0x49: ADS1115(0x49)
        }

        self.sensor_map = {
            'tc1': (0x48, 0, 'temp'),
            'tc2': (0x48, 1, 'temp'),
            'tc3': (0x48, 3, 'temp'),
            'pt1': (0x48, 2, 'press'),
            'tc4': (0x49, 0, 'temp'),
            'tc5': (0x49, 1, 'temp'),
            'tc6': (0x49, 3, 'temp'),
            'pt2': (0x49, 2, 'press'),
        }

    def _read_sensor(self, key):
        if key not in self.sensor_map:
            raise AttributeError(f"No such sensor: {key}")

        addr, pin, kind = self.sensor_map[key]
        adc = self.adcs[addr]

        if kind == 'temp':
            return adc.temperature(pin, offset=0)
        elif kind == 'press':
            return adc.pressure(pin)
        else:
            raise ValueError("Invalid sensor type")

    def __getattr__(self, name):
        if name.lower() in self.sensor_map:
            return self._read_sensor(name.lower())
        raise AttributeError(f"'SensorBoard' object has no attribute '{name}'")


def main():
    # Leave empty for now
    pass


if __name__ == '__main__':
    main()
