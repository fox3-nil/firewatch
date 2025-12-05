import time
import struct
from smbus2 import SMBus, i2c_msg

I2C_ADDR = 0x44
I2C_BUS_NO = 1

CMD_MEASURE_HIGHREP = [0x2C, 0x06]

def sensor_oneshot():
	try:
		with SMBus(I2C_BUS_NO) as bus:

			write_msg = i2c_msg.write(I2C_ADDR, CMD_MEASURE_HIGHREP)

			bus.i2c_rdwr(write_msg)

			time.sleep(0.05)

			read_msg = i2c_msg.read(I2C_ADDR, 6)

			bus.i2c_rdwr(read_msg)

			data = list(read_msg)

			raw_temp = (data[0] << 8) | data[1]
			raw_hum = (data[3] << 8) | data[4]

			etemp = -45.0 + 175.0 * (raw_temp / 65535.0)
			ehumd = 100.0 * (raw_hum / 65535.0)

			return etemp, ehumd

	except Exception as e:
		print(f"Error reading sensor: {e}")
		return None, None
