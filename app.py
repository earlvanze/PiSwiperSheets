#!/usr/bin/python3

# MagTek MSR100 Mini Swipe Card Reader
# Written By: Jeffrey Ness
# 
# Some Thanks need to go out to
# http://www.micahcarrick.com/credit-card-reader-pyusb.html
# for helping me get on the right track
# With 16x2 LCD Support via Adafruit
# https://learn.adafruit.com/drive-a-16x2-lcd-directly-with-a-raspberry-pi/

from __future__ import print_function
from subprocess import Popen, PIPE
from time import sleep
from datetime import datetime
from select import select
import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd
import sys
import os.path
import usb.core
import usb.util
import traceback
import pickle
import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Begin Google Sheets Setup
# You should change these to match your own spreadsheet
if os.path.exists('gsheet_id.txt'):
    with open('gsheet_id.txt', 'r') as file:
       json_repr = file.readline()
       data = json.loads(json_repr)
       GSHEET_ID = data["GSHEET_ID"]
       RANGE_NAME = data["RANGE_NAME"]
else:
    GSHEET_ID = '19SdvkZeAnz8awjfj-RjgQ_XlAAswBSa-2SOPomoN9xs'
    RANGE_NAME = 'Field Center Sign-In!A:A'
    
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]


# Begin Magnetic Card Reader Setup
# MagTek Device MSR90 Mini Swipe
vendorid = 0xc216
productid = 0x0180

# Define our Character Map per Reference Manual
# http://www.magtek.com/documentation/public/99875206-17.01.pdf

chrMap = {
    4:  'a',
    5:  'b',
    6:  'c',
    7:  'd',
    8:  'e',
    9:  'f',
    10: 'g',
    11: 'h',
    12: 'i',
    13: 'j',
    14: 'k',
    15: 'l',
    16: 'm',
    17: 'n',
    18: 'o',
    19: 'p',
    20: 'q',
    21: 'r',
    22: 's',
    23: 't',
    24: 'u',
    25: 'v',
    26: 'w',
    27: 'x',
    28: 'y',
    29: 'z',
    30: '1',
    31: '2',
    32: '3',
    33: '4',
    34: '5',
    35: '6',
    36: '7',
    37: '8',
    38: '9',
    39: '0',
    40: '\n',
    41: 'KEY_ESCAPE',
    42: 'KEY_BACKSPACE',
    43: '\t',
    44: ' ',
    45: '-',
    46: '=',
    47: '[',
    48: ']',
    49: '\\',
    51: ';',
    52: '\'',
    53: '`',
    54: ',',
    55: '.',
    56: '/',
    57: 'KEY_CAPSLOCK'
}

shiftchrMap = {
    4:  'A',
    5:  'B',
    6:  'C',
    7:  'D',
    8:  'E',
    9:  'F',
    10: 'G',
    11: 'H',
    12: 'I',
    13: 'J',
    14: 'K',
    15: 'L',
    16: 'M',
    17: 'N',
    18: 'O',
    19: 'P',
    20: 'Q',
    21: 'R',
    22: 'S',
    23: 'T',
    24: 'U',
    25: 'V',
    26: 'W',
    27: 'X',
    28: 'Y',
    29: 'Z',
    30: '!',
    31: '@',
    32: '#',
    33: '$',
    34: '%',
    35: '^',
    36: '&',
    37: '*',
    38: '(',
    39: ')',
    40: '\n',
    41: 'KEY_ESCAPE',
    42: 'KEY_BACKSPACE',
    43: '\t',
    44: ' ',
    45: '_',
    46: '+',
    47: '{',
    48: '}',
    49: '|',
    51: ':',
    52: '"',
    53: '~',
    54: '<',
    55: '>',
    56: '?',
    57: 'KEY_CAPSLOCK'
}

# find our device by id
device = usb.core.find(idVendor=vendorid, idProduct=productid)
if device is None:
    raise Exception('Could not find USB Card Reader')

# remove device from kernel, this should stop
# reader from printing to screen and remove /dev/input
if device.is_kernel_driver_active(0):
    try:
        device.detach_kernel_driver(0)
    except usb.core.USBError as e:
        raise Exception("Could not detach kernel driver: %s" % str(e))

# load our devices configuration
try:
    device.set_configuration()
    device.reset()
except usb.core.USBError as e:
    raise Exception("Could not set configuration: %s" % str(e))

# Begin LCD Setup
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

def main():
    # get device endpoint information
    endpoint = device[0][(0,0)][0]

    swiped = False
    data = []
    datalist = []
    print("Swipe card:")
    show_ip = True
    
    while True:
     
        # show current ip address or date and time
        lcd_line_1 = datetime.now().strftime('%m/%d %H:%M:%S\n')

        lcd_line_2 = ip_address if show_ip else "Swipe card..."

        # read card swiper
        while True:
            try:
                results = device.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize, timeout=5)
                if results:
                    data += results
                    datalist.append(results)
                    swiped = True

            except usb.core.USBError as e:
                if e.args[1] == 'Operation timed out' and swiped:
                    break # timeout and swiped means we are done

        # create a list of 8 bit bytes and remove empty bytes
        ndata = []
        for d in datalist:
            if d.tolist() != [0, 0, 0, 0, 0, 0, 0, 0]:
                ndata.append(d.tolist())

        # parse over our bytes and create string to final return
        sdata = ''
        for n in ndata:
            #print(n[0], n[2], chrMap[n[2]], shiftchrMap[n[2]])
            # handle non shifted letters
            if n[2] in chrMap and n[0] == 0:
                sdata += chrMap[n[2]]
                
            # handle shifted letters
            if n[2] in shiftchrMap and n[0] != 0:
                sdata += shiftchrMap[n[2]]

        lcd.clear()
        if sdata:
            try:
                tdata = ''.join(sdata).split('^')
                print(tdata)
                card_num = tdata[0].strip('%B')
                last_name, first_name = tdata[1].strip().split('/')
                print(first_name, last_name, card_num)
                lcd_line_2 = "Hi, {0}!".format(first_name.title())
            except Exception as err:
                traceback.print_exc()
                lcd_line_2 = str(err.args[0])
            lcd_line_1 = datetime.now().strftime('%m/%d %H:%M:%S\n')
            lcd.message = lcd_line_1 + lcd_line_2
            
            # Append to Google Sheet
            try:
                output_data = [[datetime.now().strftime('%m/%d/%y %H:%M:%S'), sdata]]
                result = append_to_gsheet(output_data, GSHEET_ID, RANGE_NAME)
                print(result)
                lcd_line_2 = result
            except Exception as err:
                traceback.print_exc()
                lcd_line_2 = str(err.args[0])
            lcd_line_1 = datetime.now().strftime('%m/%d %H:%M:%S\n')
            lcd.message = lcd_line_1 + lcd_line_2
            sleep(1)

            # Reset
            lcd.clear()
            data = []
            datalist = []

        try:
            # combine both lines into one update to the display
            lcd.message = lcd_line_1 + lcd_line_2
            show_ip = not show_ip
        except:
            traceback.print_exc()
            pass
        
        sleep(1)


def append_to_gsheet(output_data=[], gsheet_id = GSHEET_ID, range_name = RANGE_NAME):
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    body = {
        'values': output_data
    }
    try:
        result = service.spreadsheets().values().append(
            spreadsheetId=gsheet_id, range=range_name,
            valueInputOption='USER_ENTERED', body=body).execute()
        message = ('{0} rows updated.'.format(result.get('updates').get('updatedRows')))
        return message
    except Exception as err:
        traceback.print_exc()
        return json.loads(err.content.decode('utf-8'))['error']['message']


if __name__ == '__main__':
    main()
