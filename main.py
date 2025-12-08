import json
import time
from internaltnh import get_temperature, get_humidity
import externaltnh
from getnetinf import get_mac
from camera import camera
from thermal_cam import thermal_camera
import base64
import string

def getSensorData(NoIR,MLX):
	time.sleep(1)
	itemp = get_temperature()
	ihumd = get_humidity()
	etemp, ehumd = externaltnh.sensor_oneshot()
	snapshot = NoIR.capture_photo()
	#mlx_data = MLX.mlx_frame()
	data = {
		"mac": get_mac(),
		"itemp": float(f"{itemp:.2f}"),
		"etemp": float(f"{etemp:.2f}"),
		"ihumd": float(f"{ihumd:.2f}"),
		"ehumd": float(f"{ehumd:.2f}"),
		#"thermal_cam": mlx_data,
		"snapshot": snapshot
	}

	with open("readings.json", "w") as f:
		json.dump(data, f, indent=4)

def main():
	picam3 = camera()
	thermal_cam = thermal_camera()
	try:
		while True:
			getSensorData(picam3, thermal_cam)
			time.sleep(0.5)
	except KeyboardInterrupt:
		print("Shutting down system")
		sys.close(0)
	finally:
		print("Closing picam")
		picam3.close()


if __name__ == "__main__":
	main()
