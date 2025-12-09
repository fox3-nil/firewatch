import time
import json
import base64
import io
import subprocess
import os
import requests
from picamera2 import Picamera2
from picamera2.outputs import FfmpegOutput  # <--- MUST BE HERE

class camera:
    def __init__(self):
        self.picam = Picamera2()
        self.still_config = self.picam.create_still_configuration(main={"size": (1920, 1080)})
        self.video_config = self.picam.create_video_configuration(
            main={"size": (1920, 1080), "format": "XBGR8888"},
            controls={"FrameDurationLimits": (33333, 33333)}
        )

    def capture_photo(self):
        self.picam.configure(self.still_config)
        self.picam.start()
        time.sleep(2)
        try:
            stream = io.BytesIO()
            self.picam.capture_file(stream, format="jpeg")
            stream.seek(0)
            image_data = stream.getvalue()
            base64_bytes = base64.b64encode(image_data)
            base64_string = base64_bytes.decode('utf-8')
            return base64_string
        finally:
            self.picam.stop()

    def send_video(self, server_url, duration=5):
        filename = f"video_{int(time.time())}.mp4"
        # Changed to /tmp to avoid permission errors
        filepath = os.path.join("/tmp", filename) 

        try:
            print(f"Recording video to {filepath}...")
            self.picam.configure(self.video_config)
            
            # Prepare the output object
            output = FfmpegOutput(filepath)
            
            # Start recording using the output object
            self.picam.start_recording(output)
            
            self.picam.wait(duration)
            self.picam.stop_recording()

        except Exception as e:
            # This print will help us see exactly what fails
            print(f"CRITICAL ERROR during recording: {e}")
            import traceback
            traceback.print_exc() 
            return
        finally:
            self.picam.stop()

        print(f"Uploading to {server_url}..")

        try:
            with open(filepath, 'rb') as f:
                files = {'file': (filename, f, 'video/mp4')}
                response = requests.post(server_url, files=files, timeout=60)

            if response.status_code == 200:
                print("Upload successful!")
                # Optional: delete file after upload
                # if os.path.exists(filepath):
                #     os.remove(filepath)
            else:
                print(f"Upload failed. Server returned: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Network error during upload: {e}")