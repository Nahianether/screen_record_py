import pyautogui
import cv2
import numpy as np
import os
from datetime import datetime
import time
import sys
import argparse

# Recording settings
DEFAULT_FOLDER = "C:\\Recordings"
CLIP_DURATION = 120
FPS = 24
MAX_CLIPS = 100
SCREEN_SIZE = pyautogui.size()
OUTPUT_SIZE = (1280, 720)

def ensure_folder(path):
    """Create folder if it doesn't exist."""
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)

def get_timestamped_filename(folder):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(folder, f"recording_{timestamp}.mp4")

def record_clip(filename):
    """Record a single clip to the given filename."""
    ensure_folder(filename)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(filename, fourcc, FPS, OUTPUT_SIZE)
    if not out.isOpened():
        print(f"Error: Could not open video writer for {filename}")
        sys.exit(1)

    total_frames = int(FPS * CLIP_DURATION)
    frame_interval = 1 / FPS

    print(f"Recording clip: {filename} ({total_frames} frames)")
    start_time = time.time()

    for _ in range(total_frames):
        frame_start = time.time()

        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame = cv2.resize(frame, OUTPUT_SIZE)
        out.write(frame)

        elapsed = time.time() - frame_start
        time.sleep(max(0, frame_interval - elapsed))

    out.release()
    duration = time.time() - start_time
    print(f"Finished recording clip: {filename} (Actual duration: {duration:.2f}s)")

def main():
    parser = argparse.ArgumentParser(description="Record screen video.")
    parser.add_argument("--output", help="Path to output .mp4 file")
    args = parser.parse_args()

    try:
        clip_count = 0
        while clip_count < MAX_CLIPS:
            output_path = args.output or get_timestamped_filename(DEFAULT_FOLDER)
            record_clip(output_path)
            clip_count += 1
            if args.output:
                break  # only one clip if explicit path given
            time.sleep(1)
    except KeyboardInterrupt:
        print("Recording stopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
