import time
import json
import base64
import io
import subprocess
from picamera2 import Picamera2


class camera:
	'''
	The Picam should be configured 

	picam2 = Picamera2()
	pic_config = picam2.create_still_configuration()

	'''

	def capture_photo():
		#Configure the selected piCam for photos
    	#Let the camera 'wake up' before taking the photo
		picam = Picamera2()
		pic_config = picam.create_still_configuration()
		picam.configure(pic_config)
		picam.start()
		time.sleep(2)
		try:
			stream = io.BytesIO()
            picam.capture_file(stream, format="jpeg")
            	
            stream.seek(0)
			image_data = stream.getvalue()

			base64_bytes = base64.b64encode(image_data)

			base64_string = base64_bytes.decode('utf-8')

			return base64_string

		finally:
			picam.stop()
			picam.close()

	def video_stream():
		picam2 = Picamera2()
		
    		#RTMP_URL = "rtmp://x.x.x.x/live/mystream"
		UDP_URL = "udp://192.168.1.50:1234"
		WIDTH = 1280
		HEIGHT = 720
		FRAMERATE = 30
		BITRATE = 2000000  # 2Mbps

		def stream_video():
			ffmpeg_cmd = [
			'ffmpeg',
			'-re',                        # Read input at native frame rate
			'-f', 'h264',                 # Input format is raw H.264
			'-i', 'pipe:0',               # Read from Stdin
			'-c:v', 'copy',               # Copy the video stream (no re-encoding needed!)
			'-an',                        # No audio
			'-f', 'flv',                  # Output format (FLV is standard for RTMP)
			#RTMP_URL
			UDP_URL
			]

			# 2. Start the FFmpeg subprocess
			# stdin=subprocess.PIPE allows us to write data to it
			process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

			# Configure video mode
			config = picam2.create_video_configuration(
			main={"size": (WIDTH, HEIGHT), "format": "XBGR8888"}, # Format doesn't strictly matter here as we use encoder output
			controls={"FrameDurationLimits": (1000000 // FRAMERATE, 1000000 // FRAMERATE)}
			)
			picam2.configure(config)
			picam2.start()

			#print(f"Streaming to {RTMP_URL}...")
			print(f"Streaming to {UDP_URL}")
			print("Press Ctrl+C to stop.")

			try:
				# 4. The Loop: Capture and Write
				# We start recording directly to the FFmpeg process's stdin
				# 'format="h264"' ensures the Pi hardware does the compression
				picam2.start_recording(process.stdin, format="h264")

				# Keep the script running while recording happens in the background
				while True:
					time.sleep(1)
					# Optional: Check if ffmpeg crashed
					if process.poll() is not None:
						print("FFmpeg process exited unexpectedly.")
					break

			except KeyboardInterrupt:
				print("\nStopping stream...")
			except BrokenPipeError:
				print("FFmpeg pipe closed (server disconnected?)")
			finally:
				# 5. Cleanup
				picam2.stop_recording()
				picam2.stop()
				picam2.close()
				process.terminate()
