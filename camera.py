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
        filepath = os.path.join("/tmp", filename)

        try:
            print(f"Recording video to {filepath}...")
            # 1. Configure the camera
            self.picam.configure(self.video_config)
            
            # 2. Start and record directly to the file path
            # This method correctly handles the encoder and output internally
            # It records for the specified duration or until stop_recording() is called.
            self.picam.start_and_record_video(filepath, duration=duration)
            
            # Since duration is passed, it internally stops the recording after that time.
            # Explicitly calling stop_recording is often unnecessary here, but 
            # we must call self.picam.stop() to release the camera.

        except Exception as e:
            # Removed the original error handling block for brevity, but you should keep it.
            print(f"CRITICAL ERROR during recording: {e}")
            import traceback
            traceback.print_exc()
            return
        finally:
            self.picam.stop() # Always stop the camera after the operation is complete

        # --- Upload Logic (remains the same) ---
        print(f"Uploading to {server_url}..")
        # ... (rest of the upload code)
        try:
            with open(filepath, 'rb') as f:
                files = {'file': (filename, f, 'video/mp4')}
                response = requests.post(server_url, files=files, timeout=60)

            if response.status_code == 200:
                print("Upload successful!")
            else:
                print(f"Upload failed. Server returned: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Network error during upload: {e}")