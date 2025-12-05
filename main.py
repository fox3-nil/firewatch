import json
import time
from internaltnh import get_temperature, get_humidity
import externaltnh
from getnetinf import get_mac
from camera import camera
import base64
import string

def getSensorData():
	time.sleep(1)
	itemp = get_temperature()
	ihumd = get_humidity()
	etemp, ehumd = externaltnh.sensor_oneshot()
	snapshot = camera.capture_photo()
	data = {
		"mac": get_mac(),
		"itemp": float(f"{itemp:.2f}"),
		"etemp": float(f"{etemp:.2f}"),
		"ihumd": float(f"{ihumd:.2f}"),
		"ehumd": float(f"{ehumd:.2f}"),
		"snapshot": snapshot
	}

	with open("readings.json", "w") as f:
		json.dump(data, f, indent=4)

def main():
	while True:
		getSensorData()
		time.sleep(0.5)

if __name__ == "__main__":
	main()
