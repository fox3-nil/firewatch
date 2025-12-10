#!/bin/bash

# This program runs the command to start a serial monitor for wired debugging of the FireWatch system.

echo "Installing minicom serial monitor"
sudo apt install minicom

echo "Running serial monitor for wired debugging"
minicom -b 115200 -o -D /dev/ttyUSB0