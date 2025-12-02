from getmac import get_mac_address
import json

def get_mac():
	mac_address = get_mac_address()
	return mac_address
'''
def write_latest(mac):
	data = {
		"mac": mac,
	}

	with open("readings.json", "w") as f:
		json.dump(data, f, indent=4)

def main():
	mac = get_mac()
	print(f"MAC Address (using getmac): {get_mac_address()}")
	write_latest(mac)

if __name__ == "__main__":
	main()

'''
