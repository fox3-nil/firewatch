import RPi.GPIO as GPIO
import board
import time
from adafruit_ads1x15 import ADS1015, AnalogIn, ads1x15
import math

i2c = board.I2C()
ads_anemometer = ADS1015(i2c,gain = 2/3, address=0x49) #alternate address

wind_vane = AnalogIn(ads_anemometer, ads1x15.Pin.A0)

Anemometer_PIN = 17 #GPIO Pin on raspi

measure_interval = 5 #Time given to measure pulses from speed sensor

#GPIO channels used for the anemometer
GPIO.setmode(GPIO.BCM)
GPIO.setup(Anemometer_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP) #setup GPIO channel for anemometer



K = 0.667 #conversion constant from mph to m/s

#Global variable to store pulse count to use as interrupt
pulse_count = 0
last_event_time = time.time() #Used for debouncing

def wind_vane_direction():
    V_IN = 5.0
    R2 = 10000 #static transistor
    wind_vane_angle = {
		#Resistance : Angle
		33000.0 : 0,
		6570.0 : 22.5,
		8200.0 : 45,
		891.0 : 67.5,
		1000.0 : 90,
		688.0 : 112.5,
		2200.0 : 135,
		1410.0 : 157.5,
		3900.0 : 180,
		3140.0 : 202.5,
		16000.0 : 225,
		14120.0 : 247.5,
		120000.0 : 270,
		42120.0 : 292.5,
		64900.0 : 315,
		21880.0 : 337.5,
	}
    
    measured_R = (wind_vane.voltage * R2) / (V_IN - wind_vane.voltage) #
    
    key_r = closest_resistance(measured_R, wind_vane_angle)
    
    return wind_vane_angle[key_r]

def closest_resistance(R1, direction_key):
    closest_resistance = None
    min_difference = float('inf')
     
    for key_r in direction_key.keys():
         current_difference = abs(R1 - key_r)
         
         if current_difference < min_difference:
             min_difference = current_difference
             closest_resistance = key_r
    return closest_resistance

def spin_callback(channel): #interrupt to count pulse_count
	global pulse_count, last_event_time

	current_time = time.time()
	if current_time - last_event_time > 0.005 : #minimum interval of 5ms
		pulse_count += 1
	last_event_time = current_time

def calculate_wind_speed():
	"""
	Calculates the wind speed based on the accumulated pulses.
	"""
	global pulse_count

    	# Calculate the frequency (Hz)
	frequency_hz = pulse_count / measure_interval

	# Calculate the wind speed in meters per second (m/s)
	wind_speed_ms = frequency_hz * K
	# Calculate the wind speed in miles per hour (MPH) for context
	wind_speed_mph = wind_speed_ms * 2.237
	# Reset the counter for the next interval
	pulse_count = 0

	return wind_speed_ms, wind_speed_mph, frequency_hz

try:
	GPIO.add_event_detect(
    	    Anemometer_PIN, 
    	    GPIO.FALLING, 
    	    callback=spin_callback, 
     	   bouncetime=20
    	)
	print(f"--- Wind Speed Monitor Initialized ---")
	print(f"Monitoring BCM Pin {Anemometer_PIN} every {measure_interval} seconds.")
    
	while True:
        # Wait for the defined measurement interval
		time.sleep(measure_interval)
        
        # Perform calculation
		speed_ms, speed_mph, frequency = calculate_wind_speed()
  
		current_angle = wind_vane_direction()
        # Print results
		print(f"--Current Angle: {current_angle} degrees")
        # print(f"--- Measurement ({time.strftime('%H:%M:%S')}) ---")
		print(f"Pulse Frequency: {frequency:.2f} Hz")
		print(f"Wind Speed: **{speed_ms:.2f} m/s** ({speed_mph:.2f} MPH)")
        
except KeyboardInterrupt:
    print("\nMeasurement stopped by user.")

finally:
    # Always clean up the GPIO settings when the script finishes
    GPIO.cleanup()
    print("GPIO cleanup complete.")