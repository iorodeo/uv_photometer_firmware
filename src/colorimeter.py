import gc
import time
import ulab
import board
import keypad
import analogio
import digitalio
import constants
import adafruit_itertools

from light_sensor import LightSensor
from light_sensor import LightSensorOverflow
from light_sensor import LightSensorIOError

from battery_monitor import BatteryMonitor

from configuration import Configuration
from configuration import ConfigurationError

from calibrations import Calibrations
from calibrations import CalibrationsError

from menu_screen import MenuScreen
from message_screen import MessageScreen
from measure_screen import MeasureScreen

class Mode:
    MEASURE = 0
    MENU    = 1
    MESSAGE = 2
    ABORT   = 3

class Colorimeter:

    ABOUT_STR = 'About'
    RAW_SENSOR_STR = 'Raw Sensor' 
    ABSORBANCE_STR = 'Absorbance'
    TRANSMITTANCE_STR = 'Transmittance'
    DEFAULT_MEASUREMENTS = [ABSORBANCE_STR, TRANSMITTANCE_STR, RAW_SENSOR_STR]

    def __init__(self):

        self.is_startup = True
        self.measure_screen = None 
        self.message_screen = None 
        self.menu_screen = None 
        self.mode = Mode.MEASURE
        board.DISPLAY.brightness = 1.0

        self.menu_items = list(self.DEFAULT_MEASUREMENTS)
        self.menu_view_pos = 0
        self.menu_item_pos = 0
        self.is_blanked = False
        self.blank_values = ulab.numpy.ones((constants.NUM_CHANNEL,)) 
        self.channel = None

        self.pad = keypad.ShiftRegisterKeys( 
                clock=board.BUTTON_CLOCK, 
                data=board.BUTTON_OUT, 
                latch=board.BUTTON_LATCH, 
                key_count=8, 
                value_when_pressed=True,
                )

        # Load Configuration
        self.configuration = Configuration()
        try:
            self.configuration.load()
        except ConfigurationError as error:
            # Unable to load configuration file or not a dict after loading
            self.mode = Mode.MESSAGE
            self.message_screen.set_message(error)
            self.message_screen.set_to_error()
        self.channel = self.configuration.channel

        # Load calibrations and populate menu items
        self.calibrations = Calibrations()
        try:
            self.calibrations.load()
        except CalibrationsError as error: 
            # Unable to load calibrations file or not a dict after loading
            self.message_screen.set_message(error) 
            self.message_screen.set_to_error()
            self.mode = Mode.MESSAGE
        else:
            # We can load calibration, but detected errors in some calibrations
            if self.calibrations.has_errors:
                error_msg = f'errors found in calibrations file'
                self.mode = Mode.MESSAGE
                self.message_screen.set_message(error_msg)
                self.message_screen.set_to_error()

        self.menu_items.extend([k for k in self.calibrations.data])
        self.menu_items.append(self.ABOUT_STR)

        # Set default/startup measurement
        if self.configuration.startup in self.menu_items:
            self.measurement_name = self.configuration.startup
        else:
            if self.configuration.startup is not None:
                error_msg = f'startup measurement {self.configuration.startup} not found'
                self.mode = Mode.MESSAGE
                self.message_screen.set_message(error_msg)
                self.message_screen.set_to_error()
            self.measurement_name = self.menu_items[0] 

        # Setup light sensor and preliminary blanking 
        try:
            self.light_sensor = LightSensor()
        except LightSensorIOError as error:
            error_msg = f'missing sensor? {error}'
            self.mode = Mode.ABORT
            self.message_screen.set_message(error_msg,ok_to_continue=False)
            self.message_screen.set_to_abort()
        else:
            if self.configuration.gain is not None:
                self.light_sensor.gain = self.configuration.gain
            if self.configuration.integration_time is not None:
                self.light_sensor.integration_time = self.configuration.integration_time
            self.blank_sensor(set_blanked=False)
            self.measure_screen.set_not_blanked()

        # Setup up battery monitoring settings cycles 
        self.battery_monitor = BatteryMonitor()
        self.setup_menu_cycles()
        self.is_startup = False

    def setup_menu_cycles(self):
        self.gain_cycle = adafruit_itertools.cycle(constants.GAIN_TO_STR) 
        if self.configuration.gain is not None:
            while next(self.gain_cycle) != self.configuration.gain: 
                continue

        self.itime_cycle = adafruit_itertools.cycle(constants.INTEGRATION_TIME_TO_STR)
        if self.configuration.integration_time is not None:
            while next(self.itime_cycle) != self.configuration.integration_time:
                continue

        self.channel_cycle = adafruit_itertools.cycle(constants.CHANNEL_TO_STR)
        if self.configuration.channel is not None:
            while next(self.channel_cycle) != self.channel:
                continue

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, new_mode):
        self.delete_screens()
        if new_mode == Mode.MEASURE:
            self.measure_screen = MeasureScreen()
        elif new_mode in (Mode.MESSAGE, Mode.ABORT):
            self.message_screen = MessageScreen()
        elif new_mode == Mode.MENU:
            self.menu_screen = MenuScreen()
            self.menu_view_pos = 0
            self.menu_item_pos = 0
            self.update_menu_screen()
        self._mode = new_mode

    def delete_screens(self):
        self.measure_screen = None 
        self.message_screen = None 
        self.menu_screen = None 

    @property
    def num_menu_items(self):
        return len(self.menu_items)

    def incr_menu_item_pos(self):
        if self.menu_item_pos < self.num_menu_items-1:
            self.menu_item_pos += 1
        diff_pos = self.menu_item_pos - self.menu_view_pos
        if diff_pos > self.menu_screen.items_per_screen-1:
            self.menu_view_pos += 1

    def decr_menu_item_pos(self):
        if self.menu_item_pos > 0:
            self.menu_item_pos -= 1
        if self.menu_item_pos < self.menu_view_pos:
            self.menu_view_pos -= 1

    def update_menu_screen(self):
        if self.menu_screen is not None:
            n0 = self.menu_view_pos
            n1 = n0 + self.menu_screen.items_per_screen
            view_items = []
            for i, item in enumerate(self.menu_items[n0:n1]):
                led = self.calibrations.led(item)
                chan = self.calibrations.channel(item)
                if led is None and chan is None:
                    item_text = f'{n0+i} {item}' 
                elif chan is None:
                    item_text = f'{n0+i} {item} ({led})' 
                elif led is None:
                    chan_str = constants.CHANNEL_TO_STR[chan]
                    item_text = f'{n0+i} {item} ({chan_str})' 
                else:
                    chan_str = constants.CHANNEL_TO_STR[chan]
                    item = item[:8]
                    item_text = f'{n0+i} {item} ({led},{chan_str})' 
                view_items.append(item_text)
            self.menu_screen.set_menu_items(view_items)
            pos = self.menu_item_pos - self.menu_view_pos
            self.menu_screen.set_curr_item(pos)

    @property
    def is_absorbance(self):
        return self.measurement_name == self.ABSORBANCE_STR

    @property
    def is_transmittance(self):
        return self.measurement_name == self.TRANSMITTANCE_STR

    @property
    def is_raw_sensor(self):
        return self.measurement_name == self.RAW_SENSOR_STR

    @property
    def measurement_units(self):
        if self.measurement_name in self.DEFAULT_MEASUREMENTS: 
            units = None 
        else:
            units = self.calibrations.units(self.measurement_name)
        return units

    @property
    def raw_sensor_value(self):
        value = self.light_sensor.raw_values[self.channel]
        if value >= self.light_sensor.max_counts:
            raise LightSensorOverflow('light sensor reading > max_counts')
        return value

    @property
    def transmittance(self):
        value = self.raw_sensor_value
        blank_value = self.blank_values[self.channel]
        transmittance = float(value)/blank_value
        return value/blank_value

    @property
    def absorbance(self):
        absorbance = -ulab.numpy.log10(self.transmittance)
        absorbance = absorbance if absorbance > 0.0 else 0.0
        return absorbance

    @property
    def measurement_value(self):
        self.update_channel()
        if self.is_absorbance: 
            value = self.absorbance
        elif self.is_transmittance:
            value = self.transmittance
        elif self.is_raw_sensor:
            value = self.raw_sensor_value
        else:
            self.channel = self.calibrations.channel(self.measurement_name)
            try:
                value = self.calibrations.apply( 
                        self.measurement_name, 
                        self.absorbance
                        )
            except CalibrationsError as error:
                self.mode = Mode.MESSAGE
                self.message_screen.set_message(error_message)
                self.message_screen.set_to_error()
                self.measurement_name = 'Absorbance'
        return value

    def update_channel(self):
        channel = self.calibrations.channel(self.measurement_name)
        if channel is not None:
            if channel != self.channel:
                self.channel = channel
                while next(self.channel_cycle) != self.channel:
                    continue

    def blank_sensor(self, set_blanked=True):
        blank_samples = ulab.numpy.zeros( (constants.NUM_BLANK_SAMPLES,constants.NUM_CHANNEL))
        for i in range(constants.NUM_BLANK_SAMPLES):
            uva, uvb, uvc, _ = self.light_sensor.raw_values
            blank_samples[i,:] = [uva, uvb, uvc]
            time.sleep(constants.BLANK_DT)
        self.blank_values = ulab.numpy.median(blank_samples,axis=0)
        if set_blanked:
            self.is_blanked = True

    def blank_button_pressed(self, buttons):  
        if self.is_raw_sensor:
            return False
        else:
            return buttons & constants.BUTTON['blank']

    def menu_button_pressed(self, buttons): 
        return buttons & constants.BUTTON['menu']

    def up_button_pressed(self, buttons):
        return buttons & constants.BUTTON['up']

    def down_button_pressed(self, buttons):
        return buttons & constants.BUTTON['down']

    def right_button_pressed(self, buttons):
        return buttons & constants.BUTTON['right']

    def channel_button_pressed(self, buttons):
        return buttons & constants.BUTTON['left']

    def gain_button_pressed(self, buttons):
        if self.is_raw_sensor:
            return buttons & constants.BUTTON['gain']
        else:
            return False

    def itime_button_pressed(self, buttons):
        if self.is_raw_sensor:
            return buttons & constants.BUTTON['itime']
        else:
            return False

    def handle_button_press(self):
        """  
        Update state of system based on buttons pressed. This is 
        different for each operating mode. 
        """
        event = self.pad.events.get()
        if event is None:
            return
        if event.pressed:
            return

        if self.mode == Mode.MEASURE:
            if event.key_number == constants.BUTTON['blank']: 
                if not self.is_raw_sensor:
                    self.measure_screen.set_blanking()
                    self.blank_sensor()
            elif event.key_number == constants.BUTTON['menu']:
                self.mode = Mode.MENU
            elif event.key_number == constants.BUTTON['gain']: 
                self.light_sensor.gain = next(self.gain_cycle)
                self.is_blanked = False
            elif event.key_number == constants.BUTTON['itime']: 
                self.light_sensor.integration_time = next(self.itime_cycle)
                self.is_blanked = False
            elif event.key_number == constants.BUTTON['left']: 
                self.channel = next(self.channel_cycle)

        elif self.mode == Mode.MENU:
            if event.key_number == constants.BUTTON['menu']: 
                self.mode = Mode.MEASURE
            elif event.key_number == constants.BUTTON['up']: 
                self.decr_menu_item_pos()
            elif event.key_number == constants.BUTTON['down']: 
                self.incr_menu_item_pos()
            elif event.key_number == constants.BUTTON['right']: 
                selected_item = self.menu_items[self.menu_item_pos]
                if selected_item == self.ABOUT_STR:
                    self.mode = Mode.MESSAGE
                    about_msg = f'firmware version {constants.__version__}'
                    self.message_screen.set_message(about_msg) 
                    self.message_screen.set_to_about()
                else:
                    self.mode = Mode.MEASURE
                    self.measurement_name = self.menu_items[self.menu_item_pos]
            self.update_menu_screen()

        elif self.mode == Mode.MESSAGE:
            if not self.calibrations.has_errors:
                if event.key_number == constants.BUTTON['menu']:
                    self.mode = Mode.MENU




    def update_message(self): 
        if self.calibrations.has_errors:
            self.mode = Mode.MESSAGE
            error_msg = self.calibrations.pop_error()
            self.message_screen.set_message(error_msg)
            self.message_screen.set_to_error()


    def run(self):

        while True:
            # Deal with any button presses
            self.handle_button_press()

            # Update display based on the current operating mode
            if self.mode == Mode.MEASURE:

                # Get measurement and result to measurment screen
                try:
                    self.measure_screen.set_measurement(
                            self.measurement_name, 
                            self.measurement_units, 
                            self.measurement_value,
                            self.configuration.precision
                            )
                except LightSensorOverflow:
                    self.measure_screen.set_overflow(self.measurement_name)

                # Display whether or not we have blanking data. Not relevant
                # when device is displaying raw sensor data
                if self.is_raw_sensor:
                    self.measure_screen.set_blanked()
                    gain = self.light_sensor.gain
                    itime = self.light_sensor.integration_time
                    self.measure_screen.set_gain(gain)
                    self.measure_screen.set_integration_time(itime)
                else:
                    if self.is_blanked:
                        self.measure_screen.set_blanked()
                    else:
                        self.measure_screen.set_not_blanked()
                    self.measure_screen.clear_gain()
                    self.measure_screen.clear_integration_time()

                # Update and display measurement of battery voltage
                self.battery_monitor.update()
                battery_voltage = self.battery_monitor.voltage_lowpass
                self.measure_screen.set_battery(battery_voltage)
                self.measure_screen.set_channel(self.channel)
                self.measure_screen.show()

            elif self.mode == Mode.MENU:
                self.menu_screen.show()

            elif self.mode in (Mode.MESSAGE, Mode.ABORT):
                self.update_message()
                self.message_screen.show()

            time.sleep(constants.LOOP_DT)
            gc.collect()
            #print(f'alloc: {gc.mem_alloc()}, free: {gc.mem_free()}')

