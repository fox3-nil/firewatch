import json
import time
import board
import adafruit_ahtx0

i2c = board.I2C()
sensor = adafruit_ahtx0.AHTx0(i2c)


def get_temperature():
	return sensor.temperature

def get_humidity():
	return sensor.relative_humidity
