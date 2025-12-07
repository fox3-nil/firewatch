import time
import board
import busio
import subprocess
import sys
import adafruit_mlx90640

class thermal_camera:

	def __init__(self):
		self.i2c = busio.I2C(board.SCL, board.SDA, frequency=800000)

		self.mlx = adafruit_mlx90640.MLX90640(self.i2c)
		#print("MLX addr detected on I2C", [hex(i) for i in mlx.serial_number])

		self.mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ

	def mlx_frame(self):
		#print("Warming up thermal camera")
		time.sleep(2)
		frame = [0] * 768
		try:
			while(True):
				try:
					self.mlx.getFrame(frame)
					break
				except ValueError:

					# these happen, no biggie - retry
					continue

				#for h in range(24):
				#	for w in range(32):
				#		t = frame[h*32 + w]
				#break

			return frame
		except KeyboardInterrupt:
			print("\nKeyboardInterrupt caught: Stopping program gracefully.")
			sys.exit(0)


