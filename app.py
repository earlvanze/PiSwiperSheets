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
import threading
from main import *

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
data = ''

def main(data):
    while True:
        # date and time
        lcd_line_1 = datetime.now().strftime('%m/%d %H:%M:%S\n')
        
        # current ip address
        lcd_line_2 = ip_address

        # card was swiped
        if data:
            lcd.clear()
            try:
                data = ''.join(data).split('^')
                print(data)
                card_num = data[0].strip('%B')
                last_name, first_name = data[1].strip().split('/')
                print(first_name, last_name, card_num)
                lcd_line_2 = "Hi, {0}!".format(first_name.title())
            except Exception as e:
                traceback.print_exc()
                lcd_line_2 = str(e.args[0])
            finally:
                lcd.message = lcd_line_1 + lcd_line_2
                sleep(2)
                lcd.clear()
                lcd_line_2 = "Swipe card..."
        try:
            # combine both lines into one update to the display
            lcd.message = lcd_line_1 + lcd_line_2
        except:
            traceback.print_exc()
            pass
        
        sleep(1)

thread = threading.Thread(target=read_card(data), args=(data))
thread.start()

if __name__ == '__main__':
    main(data)
