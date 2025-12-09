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
#import anemometer

#test comment

SERVER_URL = "https://f-star.org:8443"


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
		"itemp": float(f"{itemp:.2f}"),
		"etemp": float(f"{etemp:.2f}"),
		"ihumd": float(f"{ihumd:.2f}"),
		"ehumd": float(f"{ehumd:.2f}"),
		"carbmono": float(f"{carbmono:.2f}"),
		"vocs": float(f"{vocs:.2f}"),
		"smoke": float(f"{smoke:.2f}"),
		"ch4": float(f"{ch4:.2f}"),
		"thermal_cam": mlx_data,
		"snapshot": snapshot
	}

	with open("readings.json", "w") as f:
		json.dump(data, f, indent=4)

	try:
		response = requests.post(SERVER_URL,json=data)

		if response.status_code == 200:
			print("Success!")
		else:
			print(f"ERROR! Status code: {response.status_code}")

	except requests.exceptions.RequestException as e:
		print(f"An error occurred during the request: {e}")


def main():
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
			time.sleep(0.5)

	except KeyboardInterrupt:
		print("Shutting down system")
		#sys.exit(0)
	finally:
		print("Closing picam")
		#picam3.close()


if __name__ == "__main__":
	main()

