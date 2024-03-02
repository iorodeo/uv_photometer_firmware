import busio
import board
import iorodeo_as7331

class LightSensor:

    AS7331_MAX_COUNT = 2**16 -1

    DEFAULT_GAIN = iorodeo_as7331.GAIN_1024X
    DEFAULT_INTEGRATION_TIME = iorodeo_as7331.INTEGRATION_TIME_32MS

    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        try:
            self._device = iorodeo_as7331.AS7331(i2c)
        except ValueError as error:
            raise LightSensorIOError(error) 

        self.gain = self.DEFAULT_GAIN
        self.integration_time = self.DEFAULT_INTEGRATION_TIME

    @property
    def max_counts(self):
        return self.AS7331_MAX_COUNT

    @property
    def gain(self):
        return self._gain

    @gain.setter
    def gain(self, value):
        self._gain = value
        self._device.gain = value

    @property
    def integration_time(self):
        return self._integration_time

    @integration_time.setter
    def integration_time(self, value):
        self._integration_time = value
        self._device.integration_time = value

    @property
    def value(self):
        return self._device.values

    @property
    def raw_values(self):
        return self._device.raw_values
        #if any([x>self.max_counts for x in raw_values]):
        #    raise LightSensorOverflow('light sensor reading > max_counts')

class LightSensorOverflow(Exception):
    pass

class LightSensorIOError(Exception):
    pass

