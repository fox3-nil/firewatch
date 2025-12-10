import os
import sys
import time
import random
import internaltnh
import externaltnh
import memssuite_probe
import serial


def clear_screen():
	os.system('cls' if os.name == 'nt' else 'clear')


ser = serial.Serial('/dev/serial0', 115200, timeout=1)

def serial_print(msg):
	print(msg)
	ser.write((msg + "\r\n").encode())

def get_sensor_values():

	#THIS IS WHERE YOU READ SENSOR VALUES AND VERIFY THEIR OUTPUT
	aht20_t = internaltnh.get_temperature()
	aht20_h = internaltnh.get_humidity()
	cht832x_t, cht832x_h = externaltnh.sensor_oneshot()
	fermion_co, fermion_voc, fermion_smoke, fermion_methane = memssuite_probe.memssuite()
	'''
	aht20_t = random.uniform(20.00, 55.00)
	aht20_h = random.uniform(45.00, 47.00)
	cht832x_t = random.uniform(10, 15)
	cht832x_h = random.uniform(55, 65)
	fermion_voc = random.uniform(0.4, 5)
	fermion_methane = random.uniform(0.4, 5)
	fermion_smoke = random.uniform(0.4, 5)
	fermion_co = random.uniform(0.4, 5)
	'''
	batterylvl = random.randint(1, 100)
	return aht20_t, aht20_h, cht832x_t, cht832x_h, fermion_voc, fermion_methane, fermion_smoke, fermion_co, batterylvl

def main():

	try:
		while True:
			itemp, ihumd, etemp, ehumd, vocs, methane, smoke, carbmono, battery = get_sensor_values()


			serial_print("\n=== SENSOR DEBUGGING TEST ===")
			serial_print(f"AHT20 Temperature:     {itemp:.2f} °C")
			serial_print(f"AHT20 Humidity:        {ihumd:.2f} %")
			serial_print(f"CHT832X Temperature:   {etemp:.2f} °C")
			serial_print(f"CHT832X Humidity:      {ehumd:.2f} %")
			serial_print(f"Fermion VOC Vout:      {vocs:.2f} V")
			serial_print(f"Fermion Methane Vout:  {methane:.2f} V")
			serial_print(f"Fermion Smoke Vout:    {smoke:.2f} V")
			serial_print(f"Fermion CO Vout:       {carbmono:.2f} V")
			serial_print(f"Battery Level:         {battery} %\n")
			serial_print("      === RESULTS ===\n")

			if itemp <= 51.66:
				serial_print("AHT20 Temperature ==============	[PASSED]")
			else:
				serial_print("AHT20 Temperature ==============	[WARNING]")
			if etemp <= 43.33:
				serial_print("CHT832X Temperature ============	[PASSED]")
			else:
				serial_print("CHT832X Temperature ============	[WARNING]")
			if 0.00 <= vocs <= 1.40:
				serial_print("VOC V OUTPUT ===================	[PASSED]")
			else:
				serial_print("VOC V OUTPUT ===================	[WARNING]")
			if 0.00 <= methane <= 2.00:
				serial_print("METHANE V OUTPUT ===============	[PASSED]")
			else:
				serial_print("METHANE V OUTPUT ===============	[WARNING]")
			if 0.00 <= smoke <= 0.5:
				serial_print("SMOKE V OUTPUT =================	[PASSED]")
			else:
				serial_print("SMOKE V OUTPUT =================	[WARNING]")
			if 0.00 <= carbmono <= 0.90:
				serial_print("CARBON MONOXIDE V OUTPUT =======	[PASSED]")
			else:
				serial_print("CARBON MONOXIDE V OUTPUT =======	[WARNING]")

			print("\n")
			time.sleep(1)

	except KeyboardInterrupt:
		serial_print("\nDEBUG STOPPED\n")
		sys.exit(0)

if __name__ == "__main__":
	main()
