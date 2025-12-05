import time
import board
import busio
import subprocess
import adafruit_mlx90640

class thermal_camera:
	i2c = busio.I2C(board.SCL, board.SDA, frequency=800000)

	mlx = adafruit_mlx90640.MLX90640(i2c)
	print("MLX addr detected on I2C", [hex(i) for i in mlx.serial_number])

	mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ

	def mlx_frame:
		#print("Warming up thermal camera")
		#sleep(0.5)
		#frame = [0] * 768
		while(True):
			try:
        			mlx.getFrame(frame)
    			except ValueError:
        		# these happen, no biggie - retry
        			continue

	    		for h in range(24):
				for w in range(32):
            				t = frame[h*32 + w]
			break
		return frame

