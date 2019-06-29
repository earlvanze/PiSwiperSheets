from evdev import InputDevice, categorize, ecodes
from select import select
from subprocess import Popen, PIPE
from time import sleep
from datetime import datetime
import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd
import sys
import os
import traceback

# Initialize card reader device
swiper = InputDevice("/dev/input/event0") # magswipe card reader

scancodes = {
    # Scancode: ASCIICode
    0: None, 1: u'ESC', 2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8',
    10: u'9', 11: u'0', 12: u'-', 13: u'=', 14: u'BKSP', 15: u'TAB', 16: u'Q', 17: u'W', 18: u'E', 19: u'R',
    20: u'T', 21: u'Y', 22: u'U', 23: u'I', 24: u'O', 25: u'P', 26: u'[', 27: u']', 28: u'CRLF', 29: u'LCTRL',
    30: u'A', 31: u'S', 32: u'D', 33: u'F', 34: u'G', 35: u'H', 36: u'J', 37: u'K', 38: u'L', 39: u';',
    40: u'"', 41: u'`', 42: u'LSHFT', 43: u'\\', 44: u'Z', 45: u'X', 46: u'C', 47: u'V', 48: u'B', 49: u'N',
    50: u'M', 51: u',', 52: u'.', 53: u'/', 54: u'RSHFT', 57: u' ', 100: u'?'
}

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

while True:
    # date and time
    lcd_line_1 = datetime.now().strftime('%m/%d %H:%M:%S\n')

    # current ip address
    lcd_line_2 = ip_address
    
    # listen to card swiper
    r,w,x = select([sys.stdin.fileno()], [], [], 0.1)

    if sys.stdin.fileno() in r:
        data = os.read(sys.stdin.fileno(), 4096)
        if not len(data):
            break
        data = data.decode('UTF-8')

        try:
            data = data.split(b'\x1b'.decode('UTF-8'))
            data = " ".join(data).split('^')
            print(data)
            card_num = data[0].strip('%B')
            last_name, first_name = data[1].strip().split('/')
            print(first_name, last_name, card_num)
            lcd_line_2 = "Hi, {0}!".format(first_name.capitalize())
            sleep(2)
        except Exception as e:
            traceback.print_exc()
            lcd_line_2 = e

    # combine both lines into one update to the display
    lcd.message = lcd_line_1 + lcd_line_2

    sleep(1)
