from evdev import InputDevice, categorize, ecodes
from select import select
from subprocess import Popen, PIPE
from time import sleep
from datetime import datetime
from threading import Thread
import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd
import asyncio

# Initialize card reader
swiper = InputDevice("/dev/input/event0") # magswipe card reader

scancodes = {
    0: None,
    1: u'ESC',
    2: u'1',
    3: u'2',
    4: u'3',
    5: u'4',
    6: u'5',
    7: u'6',
    8: u'7',
    9: u'8',
    10: u'9',
    11: u'0',
    12: u'-',
    13: u'=',
    14: u'BKSP',
    15: u'\t',
    16: u'Q',
    17: u'W',
    18: u'E',
    19: u'R',
    20: u'T',
    21: u'Y',
    22: u'U',
    23: u'I',
    24: u'O',
    25: u'P',
    26: u'[',
    27: u']',
    28: u'\n',
    29: u'LCTRL',
    30: u'A',
    31: u'S',
    32: u'D',
    33: u'F',
    34: u'G',
    35: u'H',
    36: u'J',
    37: u'K',
    38: u'L',
    39: u';',
    40: u"'",
    41: u'`',
    42: u'LSHFT',
    43: u'\\',
    44: u'Z',
    45: u'X',
    46: u'C',
    47: u'V',
    48: u'B',
    49: u'N',
    50: u'M',
    51: u',',
    52: u'.',
    53: u'/',
    54: u' ',
    55: u'*',
    56: u'LALT',
    57: u'\s',
    58: u'CAPS',
    59: u'F1',
    60: u'F2',
}

# Modify this if you have a different sized character LCD
lcd_columns = 16
lcd_rows = 2

# compatible with all versions of RPI as of Jan. 2019
# v1 - v3B+
lcd_rs = digitalio.DigitalInOut(board.D22)
lcd_en = digitalio.DigitalInOut(board.D17)
lcd_d4 = digitalio.DigitalInOut(board.D25)
lcd_d5 = digitalio.DigitalInOut(board.D24)
lcd_d6 = digitalio.DigitalInOut(board.D23)
lcd_d7 = digitalio.DigitalInOut(board.D18)


# Initialise the lcd class
lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6,
                                      lcd_d7, lcd_columns, lcd_rows)

# looking for an active Ethernet or WiFi device
def find_interface():
    find_device = "ip addr show"
    interface_parse = run_cmd(find_device)
    for line in interface_parse.splitlines():
        if "state UP" in line:
            dev_name = line.split(':')[1]
    return dev_name

# find an active IP on the first LIVE network device
def parse_ip():
    find_ip = "ip addr show %s" % interface
    find_ip = "ip addr show %s" % interface
    ip_parse = run_cmd(find_ip)
    for line in ip_parse.splitlines():
        if "inet " in line:
            ip = line.split(' ')[5]
            ip = ip.split('/')[0]
    return ip

# run unix shell command, return as ASCII
def run_cmd(cmd):
    p = Popen(cmd, shell=True, stdout=PIPE)
    output = p.communicate()[0]
    return output.decode('ascii')

# wipe LCD screen before we start
lcd.clear()

# before we start the main loop - detect active network device and ip address
sleep(2)
interface = find_interface()
ip_address = parse_ip()

lcd_line_2 = ""

#print(swiper.capabilities(verbose=True))

async def helper_old(swiper, lcd_line_2):
    async for event in swiper.async_read_loop():
        if event.type == ecodes.EV_KEY and event.value == 1:
            data = categorize(event)  # Save the event temporarily to introspect it
            key_lookup = scancodes.get(data.scancode) or u'blah{}'.format(data.scancode)  # Lookup or return UNKNOWN:XX
            lcd_line_2 += key_lookup
            print(lcd_line_2)

while True:
    lcd_line_2 = input()
    print(lcd_line_2)
    # date and time
    lcd_line_1 = datetime.now().strftime('%m/%d %H:%M:%S\n')

    # combine both lines into one update to the display
    lcd_line_2 = lcd_line_2.split('^.')[0].strip()
    print(lcd_line_2)
    lcd.message = lcd_line_1 + lcd_line_2
            
