import time
import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from collections import deque

class WindSensor:
    def __init__(self, window_size=10):
        # --- Configuration Constants ---
        self.SENSOR_MAX_VOLTS = 5.0
        self.SENSOR_OFFSET_VOLTS = 0.0  # Set to 0.4 if your sensor has a live-zero
        self.SENSOR_MAX_MPH = 40.0
        self.DIVIDER_RATIO = 2.0
        
        # --- Rolling Average Buffer ---
        # deque with maxlen automatically pops old items when new ones are added
        self.readings = deque(maxlen=window_size)
        
        # --- Hardware Setup ---
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.ads = ADS.ADS1015(self.i2c)
        self.ads.gain = 1
        self.chan = AnalogIn(self.ads, ADS.P0)

    def _get_instant_speed(self):
        """Internal function to read the immediate physical value."""
        pin_voltage = self.chan.voltage
        sensor_voltage = pin_voltage * self.DIVIDER_RATIO
        
        if sensor_voltage <= self.SENSOR_OFFSET_VOLTS:
            return 0.0
            
        voltage_range = self.SENSOR_MAX_VOLTS - self.SENSOR_OFFSET_VOLTS
        speed = ((sensor_voltage - self.SENSOR_OFFSET_VOLTS) / voltage_range) * self.SENSOR_MAX_MPH
        return speed

    def get_smoothed_speed(self):
        """
        Reads the current speed, adds it to the history buffer,
        and returns the average of the buffer.
        """
        # 1. Get current reading
        instant_speed = self._get_instant_speed()
        
        # 2. Add to buffer (oldest reading is automatically removed if full)
        self.readings.append(instant_speed)
        
        # 3. Calculate Average
        if len(self.readings) == 0:
            return 0.0
        
        average_speed = sum(self.readings) / len(self.readings)
        return average_speed

# --- Main Execution Block ---
if __name__ == "__main__":
    # Initialize the sensor with a smoothing window of 10 samples
    anemometer = WindSensor(window_size=10)
    
    print("Reading smoothed wind data...")
    print("-" * 40)
    
    try:
        while True:
            # We call get_smoothed_speed() to do all the math for us
            avg_speed = anemometer.get_smoothed_speed()
            
            # Tip: You can access the raw buffer if you ever need to debug
            # raw_last = anemometer.readings[-1] 
            
            print(f"Wind Speed (Avg): {avg_speed:.2f} mph")
            
            # Taking a sample every 0.1s with a window of 10 
            # means we are averaging the last 1 second of data.
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nStopped.")
