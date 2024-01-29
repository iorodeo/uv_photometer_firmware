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
        self.channel = 2

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
        #-----------------------------------------------------
        # TODO: need some way to indicate overflow for channel
        # ----------------------------------------------------
        value = self._device.values[self.channel]
        return value

    @property
    def raw_value(self):
        raw_value = self._device.raw_values[self.channel]
        if raw_value >= self.max_counts:
            raise LightSensorOverflow('light sensor reading > max_counts')
        return raw_value

class LightSensorOverflow(Exception):
    pass

class LightSensorIOError(Exception):
    pass

