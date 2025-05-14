import pyautogui
import cv2
import numpy as np
import os
from datetime import datetime
import time
import sys
import argparse

# Defaults
DEFAULT_FOLDER = "C:\\Recordings"
DEFAULT_DURATION = 120
DEFAULT_FPS = 24
DEFAULT_RESOLUTION = (1280, 720)

def ensure_folder(path):
    """Ensure parent folder exists for the given file path."""
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)

def get_timestamped_filename(folder):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(folder, f"recording_{timestamp}.mp4")

def parse_resolution(res_str):
    """Parse resolution string '1280x720' into a tuple."""
    try:
        width, height = map(int, res_str.lower().split("x"))
        return (width, height)
    except:
        raise argparse.ArgumentTypeError("Resolution must be in the format WIDTHxHEIGHT (e.g., 1280x720)")

def record_clip(filename, duration, fps, resolution):
    ensure_folder(filename)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(filename, fourcc, fps, resolution)
    if not out.isOpened():
        print(f"Error: Could not open video writer for {filename}")
        sys.exit(1)

    total_frames = int(fps * duration)
    frame_interval = 1 / fps

    print(f"Recording clip: {filename} ({total_frames} frames at {fps} FPS, {resolution[0]}x{resolution[1]})")
    start_time = time.time()

    for _ in range(total_frames):
        frame_start = time.time()

        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame = cv2.resize(frame, resolution)
        out.write(frame)

        elapsed = time.time() - frame_start
        time.sleep(max(0, frame_interval - elapsed))

    out.release()
    duration_actual = time.time() - start_time
    print(f"Finished recording: {filename} (Actual duration: {duration_actual:.2f}s)")

def main():
    parser = argparse.ArgumentParser(description="Screen Recorder")
    parser.add_argument("--output", help="Output path for .mp4 file")
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION, help="Recording duration in seconds")
    parser.add_argument("--fps", type=int, default=DEFAULT_FPS, help="Frames per second")
    parser.add_argument("--resolution", type=parse_resolution, default=DEFAULT_RESOLUTION,
                        help="Output resolution (format: WIDTHxHEIGHT, e.g. 1280x720)")
    args = parser.parse_args()

    output_path = args.output or get_timestamped_filename(DEFAULT_FOLDER)
    
    try:
        record_clip(output_path, args.duration, args.fps, args.resolution)
    except KeyboardInterrupt:
        print("Recording interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
