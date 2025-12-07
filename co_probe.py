# Probe code for singular sensor probing

import time
import board
import busio
# import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15 import ADS1015, AnalogIn, ads1x15


i2c = board.I2C()
ads = ADS1015(i2c)

co_channel = AnalogIn(ads, ads1x15.Pin.A0)

ads.gain = 1

print("Fermion Carbon Monoxide sensor initialized")
print("-" *25)

try:
    while True:
        co_rawval = co_channel.value
        co_vltg = co_channel.voltage
        print(f"Raw Value: {co_rawval} | Voltage: {co_vltg: .4f} V")
        
        time.sleep(0.5)
        
except KeyboardInterrupt:
    print("Program interrupted by user.")