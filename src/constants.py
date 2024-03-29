import board
import collections
import iorodeo_as7331

__version__ = '0.2.0'

CALIBRATIONS_FILE = 'calibrations.json'
CONFIGURATION_FILE = 'configuration.json'
SPLASHSCREEN_BMP = 'assets/splashscreen.bmp'

LOOP_DT = 0.1
BLANK_DT = 0.05
NUM_BLANK_SAMPLES = 50 
BATTERY_AIN_PIN = board.A6

BUTTON = { 
        'left'  : 7,
        'up'    : 6, 
        'down'  : 5, 
        'right' : 4, 
        'menu'  : 3, 
        'blank' : 2, 
        'itime' : 1, 
        'gain'  : 0, 
        }

COLOR_TO_RGB = collections.OrderedDict([ 
    ('black'  , 0x000000), 
    ('gray'   , 0x818181), 
    ('red'    , 0xff0000), 
    ('green'  , 0x00ff00),
    ('blue'   , 0x0000ff),
    ('white'  , 0xffffff), 
    ('orange' , 0xffb447),
    ('purple' , 0x9d4edd),
    ])

STR_TO_GAIN = collections.OrderedDict([ 
    ('1x',    iorodeo_as7331.GAIN_1X),
    ('2x',    iorodeo_as7331.GAIN_2X),
    ('4x',    iorodeo_as7331.GAIN_4X),
    ('8x',    iorodeo_as7331.GAIN_8X),
    ('16x',   iorodeo_as7331.GAIN_16X),
    ('32x',   iorodeo_as7331.GAIN_32X),
    ('64x',   iorodeo_as7331.GAIN_64X),
    ('128x',  iorodeo_as7331.GAIN_128X),
    ('256x',  iorodeo_as7331.GAIN_256X),
    ('512x',  iorodeo_as7331.GAIN_512X),
    ('1024x', iorodeo_as7331.GAIN_1024X),
    ('2048x', iorodeo_as7331.GAIN_2048X),
    ])
GAIN_TO_STR = collections.OrderedDict(((v,k) for k,v in STR_TO_GAIN.items()))

STR_TO_INTEGRATION_TIME = collections.OrderedDict([ 
    ('1ms',    iorodeo_as7331.INTEGRATION_TIME_1MS),      
    ('2ms',    iorodeo_as7331.INTEGRATION_TIME_2MS),      
    ('4ms',    iorodeo_as7331.INTEGRATION_TIME_4MS),      
    ('8ms',    iorodeo_as7331.INTEGRATION_TIME_8MS),      
    ('16ms',   iorodeo_as7331.INTEGRATION_TIME_16MS),     
    ('32ms',   iorodeo_as7331.INTEGRATION_TIME_32MS),     
    ('64ms',   iorodeo_as7331.INTEGRATION_TIME_64MS),     
    ('128ms',  iorodeo_as7331.INTEGRATION_TIME_128MS),    
    ('256ms',  iorodeo_as7331.INTEGRATION_TIME_256MS),    
    ('512ms',  iorodeo_as7331.INTEGRATION_TIME_512MS),    
    #('1024ms', iorodeo_as7331.INTEGRATION_TIME_1024MS),   
    #('2048ms', iorodeo_as7331.INTEGRATION_TIME_2048MS),   
    #('4096ms', iorodeo_as7331.INTEGRATION_TIME_4096MS),   
    #('8192ms', iorodeo_as7331.INTEGRATION_TIME_8192MS),   
    #('1638ms', iorodeo_as7331.INTEGRATION_TIME_16384MS),  
    ])
INTEGRATION_TIME_TO_STR = \
    collections.OrderedDict(((v,k) for k,v in STR_TO_INTEGRATION_TIME.items()))

CHANNEL_UVA = 0
CHANNEL_UVB = 1
CHANNEL_UVC = 2
NUM_CHANNEL = 3

STR_TO_CHANNEL = collections.OrderedDict([
    ('UVA', 0), 
    ('UVB', 1),
    ('UVC', 2)
    ])
CHANNEL_TO_STR = \
        collections.OrderedDict(((v,k) for k,v in STR_TO_CHANNEL.items()))


