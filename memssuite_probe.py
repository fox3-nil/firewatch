# Probe code for full gas sensor suite (ct 4) probing

import time
import board
import busio
# import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15 import ADS1015, AnalogIn, ads1x15


i2c = board.I2C()
ads = ADS1015(i2c)

def memssuite():
	# CHANNELS -- current config ==> A0: CO, A1: VOC, A2: Smoke, A3: Methane
	co_channel = AnalogIn(ads, ads1x15.Pin.A0)
	voc_channel = AnalogIn(ads, ads1x15.Pin.A1)
	smk_channel = AnalogIn(ads, ads1x15.Pin.A2)
	ch4_channel = AnalogIn(ads, ads1x15.Pin.A3)

	ads.gain = 1

	print("MEMs sensor suite initialized")
	print("-" * 50)

	try:
		print("Probing mems sensors...")

		'''
		while True:
			print("-" * 50)
			print(f"CO SENSING: raw Value: {co_channel.value} | Voltage: {co_channel.voltage: .6f} V")
			print(f"VOC SENSING: raw Value: {voc_channel.value} | Voltage: {voc_channel.voltage: .6f} V")
			print(f"SMK SENSING: raw Value: {smk_channel.value} | Voltage: {smk_channel.voltage: .6f} V")
			print(f"CH4 SENSING: raw Value: {ch4_channel.value} | Voltage: {ch4_channel.voltage: .6f} V")
			print("-" * 50)
			time.sleep(2.0)
        	'''
	except KeyboardInterrupt:
        	print("Probing ceased.")

	return co_channel.voltage, voc_channel.voltage, smk_channel.voltage, ch4_channel.voltage
