import json
import time
from internaltnh import get_temperature, get_humidity
from getnetinf import get_mac

def getSensorData():

	data = {
		"mac": get_mac(),
		"itemp": float(f"{get_temperature():.2f}"),
		"ihumd": float(f"{get_humidity():.2f}"),
	}

	with open("readings.json", "w") as f:
		json.dump(data, f, indent=4)

def main():
	while True:
		getSensorData()
		time.sleep(1)

if __name__ == "__main__":
	main()
