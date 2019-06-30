#!/bin/bash
killall python3

nohup /usr/bin/python3 /home/pi/PiSwiperSheets/app.py > log.txt 2>&1 &
nohup /usr/bin/python3 /home/pi/PiSwiperSheets/power_switch.py > log.txt 2>&1 &
