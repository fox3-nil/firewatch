import RPi.GPIO as GPIO
import time
import math

Anemometer_PIN = 17 #GPIO Pin on raspi

measure_interval = 5 #Time given to measure pulses from speed sensor


K = 0.667 #conversion constant from mph to m/s

#Global variable to store pulse count to use as interrupt
pulse_count = 0
last_event_time = time.time() #Used for debouncing

def spin_callback(channel): #interrupt to count pulse_count
	global pulse_count, last_event_time

	current_time = time.time()
	if current_time - last_event_time > 0.005 #minimum interval of 5ms
		pulse_count += 1
	last_event_time = current_time

def calculate_wind_speed():
	"""
	Calculates the wind speed based on the accumulated pulses.
	"""
	global pulse_count

    	# Calculate the frequency (Hz)
	frequency_hz = pulse_count / MEASUREMENT_INTERVAL

	# Calculate the wind speed in meters per second (m/s)
	wind_speed_ms = frequency_hz * K
	# Calculate the wind speed in miles per hour (MPH) for context
	wind_speed_mph = wind_speed_ms * 2.237
	# Reset the counter for the next interval
	pulse_count = 0

	return wind_speed_ms, wind_speed_mph, frequency_hz
