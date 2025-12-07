import os
import time
import random

def clear_screen():
	os.system('cls' if os.name == 'nt' else 'clear')

def get_sensor_values():

	#THIS IS WHERE YOU READ SENSOR VALUES AND VERIFY THEIR OUTPUT

	aht20_t = random.randint(20, 25)
	aht20_h = random.randint(45, 55)
	cht832x_t = random.randint(10, 15)
	cht832x_h = random.randint(55, 65)
	fermion_voc = random.uniform(0.4, 3.3)
	fermion_meth = random.uniform(0.4, 3.3)
	fermion_smoke = random.uniform(0.4, 3.3)
	fermion_co = random.uniform(0.4, 3.3)
	return aht20_t, aht20_h, cht832x_t, cht832x_h, fermion_voc, fermion_meth, fermion_smoke, fermion_co

def main():
	while True:
		itemp, ihumd, etemp, ehumd, vocs, methane, smoke, mems = get_sensor_values()

		clear_screen()
		print("=== SENSOR DEBUGGING TEST ===")
		print(f"AHT20 Temperature:     {itemp} °C")
		print(f"AHT20 Humidity:        {ihumd} %")
		print(f"CHT832X Temperature:   {etemp} °C")
		print(f"CHT832X Humidity:      {ehumd} %")
		print(f"Fermion VOC Vout:      {vocs:.2f} V")
		print(f"Fermion Methane Vout:  {methane:.2f} V")
		print(f"Fermion Smoke Vout:    {smoke:.2f} V")
		print(f"Fermion CO Vout:       {mems:.2f} V")

		time.sleep(1)

if __name__ == "__main__":
	main()
