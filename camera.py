import time
import json
import base64
import io
from picamera2 import Picamera2

'''
The Picam should be configured 

picam2 = Picamera2()
pic_config = picam2.create_still_configuration()

'''

def capture_photo(picam, pic_config):
    #Configure the selected piCam for photos
    #Let the camera 'wake up' before taking the photo
    picam.configure(pic_config)
    picam.start()
    time.sleep(2)
    try:
        stream = io.BytesIO()

        stream.seek(0)
        image_data = stream.getvalue()

        base64_bytes = base64.b64encode(image_data)

        base64_string = base64.decode('utf-8')

        return base64_string
    
    finally:
        picam.stop()
        picam.close()

def video_stream(picam, picam_video_config, stream_configuration):
    #The following code is a placeholder for further configuration

    '''
    import time
    import subprocess
    from picamera2 import Picamera2

    # --- CONFIGURATION ---
    RTMP_URL = "rtmp://x.x.x.x/live/mystream"  # Replace with your endpoint
    WIDTH = 1280
    HEIGHT = 720
    FRAMERATE = 30
    BITRATE = 2000000  # 2Mbps

    def stream_video():
    # 1. Setup the FFmpeg command
    # We tell FFmpeg to expect raw H.264 data from 'pipe:0' (standard input)
    ffmpeg_cmd = [
        'ffmpeg',
        '-re',                        # Read input at native frame rate
        '-f', 'h264',                 # Input format is raw H.264
        '-i', 'pipe:0',               # Read from Stdin
        '-c:v', 'copy',               # Copy the video stream (no re-encoding needed!)
        '-an',                        # No audio
        '-f', 'flv',                  # Output format (FLV is standard for RTMP)
        RTMP_URL
    ]

    # 2. Start the FFmpeg subprocess
    # stdin=subprocess.PIPE allows us to write data to it
    process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

    # 3. Initialize Camera
    picam2 = Picamera2()
    
    # Configure video mode
    config = picam2.create_video_configuration(
        main={"size": (WIDTH, HEIGHT), "format": "XBGR8888"}, # Format doesn't strictly matter here as we use encoder output
        controls={"FrameDurationLimits": (1000000 // FRAMERATE, 1000000 // FRAMERATE)}
    )
    picam2.configure(config)
    picam2.start()

    print(f"Streaming to {RTMP_URL}...")
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

if __name__ == "__main__":
    stream_video()
    '''
    return 0