import requests
import json
import time
from internaltnh import get_temperature, get_humidity
import externaltnh
from getnetinf import get_mac
from camera import camera
from thermal_cam import thermal_camera
import base64
import string
import memssuite_probe
import sys
#import anemometer

#test comment

#SERVER_URL = "http://f-star.org:8080"
SERVER_URL = "http://10.125.161.153:8080"


def getSensorData(NoIR,MLX):
	time.sleep(1)
	itemp = get_temperature()
	ihumd = get_humidity()
	etemp, ehumd = externaltnh.sensor_oneshot()
	carbmono, vocs, smoke, ch4 = memssuite_probe.memssuite()
	snapshot = NoIR.capture_photo()
	mlx_data = MLX.mlx_frame()
	'''
	time.sleep(5)
	speed_ms, speed_mph, frequency = anemometer.calculate_wind_speed()
	'''
	data = {
		"mac": get_mac(),
		"temp_internal_c": float(f"{itemp:.2f}"),
		"temp_external_c": float(f"{etemp:.2f}"),
		"humd_internal_per": float(f"{ihumd:.2f}"),
		"humd_external_per": float(f"{ehumd:.2f}"),
		"co_v": float(f"{carbmono:.2f}"),
		"voc_v": float(f"{vocs:.2f}"),
		"smoke_v": float(f"{smoke:.2f}"),
		"methane_v": float(f"{ch4:.2f}"),
		"thermal_cam": mlx_data,
		"recent_image_data": snapshot,
		"latitude": 00.000,
		"longitude": 0.000,
		"wind_speed_mph": 100,
		"timestamp": "2025-12-09T02:25:00.000Z"
	}

	with open("readings.json", "w") as f:
		json.dump(data, f, indent=4)

	try:
		print(f"Connecting to {SERVER_URL}")
		response = requests.post(SERVER_URL,json=data)

		if response.status_code == 200:
			print("Success!")
		else:
			print(f"ERROR! Status code: {response.status_code}")

	except requests.exceptions.RequestException as e:
		print(f"An error occurred during the request: {e}")


def main(argv):
	picam3 = camera()
	thermal_cam = thermal_camera()
	try:
		'''
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(ANEMOMETER_PIN, GPIO.IN, pull_up_down=GPIO.PULL_UP)
		GPIO.add_event_detect(
			ANEMOMETER_PIN,
			GPIO.FALLING,
			callback=spin_callback,
			bouncetime=20
		)
		'''
		while True:

			getSensorData(picam3, thermal_cam)
			if(len(sys.argv) > 1 and sys.argv[1] == "record"):
				print("Recording...")
				picam3.send_video(SERVER_URL, 10)
			time.sleep(5)


	except KeyboardInterrupt:
		print("Shutting down system")
		#sys.exit(0)
	finally:
		print("Closing picam")
		#picam3.close()


if __name__ == "__main__":
	main(sys.argv)

