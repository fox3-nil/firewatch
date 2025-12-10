import RPi.GPIO as GPIO
import time
import math

Anemometer_PIN = 17 #GPIO Pin on raspi

measure_interval = 5 #Time given to measure pulses from speed sensor

#GPIO channels used for the anemometer
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()
GPIO.setup(Anemometer_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP) #setup GPIO channel for anemometer



K = 0.667 #conversion constant from mph to m/s

#Global variable to store pulse count to use as interrupt
pulse_count = 0
last_event_time = time.time() #Used for debouncing

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
        
        # Print results
        # print(f"--- Measurement ({time.strftime('%H:%M:%S')}) ---")
		print(f"Pulse Frequency: {frequency:.2f} Hz")
		print(f"Wind Speed: **{speed_ms:.2f} m/s** ({speed_mph:.2f} MPH)")
        
except KeyboardInterrupt:
    print("\nMeasurement stopped by user.")

finally:
    # Always clean up the GPIO settings when the script finishes
    GPIO.cleanup()
    print("GPIO cleanup complete.")