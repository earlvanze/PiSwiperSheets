#!/bin/bash
killall python3

nohup /usr/bin/python3 /home/pi/app.py > log.txt 2>&1 &
nohup /usr/bin/python3 /home/pi/power_switch.py > log.txt 2>&1 &
