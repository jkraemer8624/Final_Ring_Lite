#!/bin/bash
ESP_MAC="A0:DD:6C:74:7F:24"
HANDLE=0x002a
MOTION_HEX="4d 6f 74 69 6f 6e"   #HEX FOR ACII "MOTION"

PY = "/usr/bin/python3"

while true
do
    if [ "$(sudo gatttool - b A0:DD:6C:74:7F:24 --char-read - a 0x002a | awk -F':' '{print $NF}')" = " 4d 6f 74 69 6f 6e " ]
    then
        echo "Motion detected... Taking photo"
        "$PY" /capture_app/capture_photo.py
        sleep 2
    else
        echo "$(sudo gatttool - b A0:DD:6C:74:7F:24 --char-read - a 0x002a | awk -F':' '{print $NF}')"
    fi 
done