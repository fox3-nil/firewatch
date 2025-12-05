import json
import time
#from internaltnh import get_itemp, get_ihumd
import externaltnh
from getnetinf import get_mac


def getSensorData():
	time.sleep(1)
	etemp, ehumd = externaltnh.sensor_oneshot()
	data = {
		"mac": get_mac(),
#		"itemp": float(f"{temp:.2f}"),
		"etemp": float(f"{etemp:.2f}"),
#		"ihumd": float(f"{humd:.2f}"),
		"ehumd": float(f"{ehumd:.2f}")
	}

	with open("readings.json", "w") as f:
		json.dump(data, f, indent=4)

def main():
	while True:
		getSensorData()
		time.sleep(1)

if __name__ == "__main__":
	main()
