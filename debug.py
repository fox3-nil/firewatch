import os
import sys
import time
import random
import internaltnh
import externaltnh
import memssuite_probe
#import co_probe

'''
def clear_screen():
	os.system('cls' if os.name == 'nt' else 'clear')
'''
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
	fermion_voc = random.uniform(0.4, 3.3)
	fermion_meth = random.uniform(0.4, 3.3)
	fermion_smoke = random.uniform(0.4, 3.3)
	fermion_co = random.uniform(0.4, 3.3)
	'''
	batterylvl = random.randint(1, 100)
	return aht20_t, aht20_h, cht832x_t, cht832x_h, fermion_voc, fermion_methane, fermion_smoke, fermion_co, batterylvl

def main():

	GREEN = '\033[32m'
	YELLOW = '\033[33m'
	RESET = '\033[0m'

	try:
		while True:
			itemp, ihumd, etemp, ehumd, vocs, methane, smoke, carbmono, battery = get_sensor_values()

			#clear_screen()
			print("\n=== SENSOR DEBUGGING TEST ===")
			print(f"AHT20 Temperature:     {itemp:.2f} °C")
			print(f"AHT20 Humidity:        {ihumd:.2f} %")
			print(f"CHT832X Temperature:   {etemp:.2f} °C")
			print(f"CHT832X Humidity:      {ehumd:.2f} %")
			print(f"Fermion VOC Vout:      {vocs:.2f} V")
			print(f"Fermion Methane Vout:  {methane:.2f} V")
			print(f"Fermion Smoke Vout:    {smoke:.2f} V")
			print(f"Fermion CO Vout:       {carbmono:.2f} V")
			print(f"Battery Level:         {battery} %\n")
			print("      === RESULTS ===\n")
			if itemp <= 51.66:
				print("AHT20 Temperature ==============", GREEN + " [PASSED]" + RESET)
			else:
				print("AHT20 Temperature ==============", YELLOW + " [WARNING]" + RESET)
			if etemp <= 43.33:
				print("CHT832X Temperature ============", GREEN + " [PASSED]" + RESET)
			else:
				print("CHT832X Temperature ============", YELLOW + " [WARNING]" + RESET)
			if 0.00 <= vocs <= 1.40:
				print("VOC V OUTPUT ===================", GREEN + " [PASSED]" + RESET)
			else:
				print("VOC V OUTPUT ===================", YELLOW + " [WARNING]" + RESET)
			if 0.00 <= methane <= 2.00:
				print("METHANE V OUTPUT ===============", GREEN + " [PASSED]" + RESET)
			else:
				print("METHANE V OUTPUT ===============", YELLOW + " [WARNING]" + RESET)
			if 0.00 <= smoke <= 0.88:
				print("SMOKE V OUTPUT =================", GREEN + " [PASSED]" + RESET)
			else:
				print("SMOKE V OUTPUT =================", YELLOW + " [WARNING]" + RESET)
			if 0.00 <= carbmono <= 0.90:
				print("CARBON MONOXIDE V OUTPUT =======", GREEN + " [PASSED]" + RESET)
			else:
				print("CARBON MONOXIDE V OUTPUT =======", YELLOW + " [WARNING]" + RESET)

			print("\n")
			time.sleep(1)

	except KeyboardInterrupt:
		print("\nDEBUG STOPPED\n")
		sys.exit(0)

if __name__ == "__main__":
	main()
