import pyautogui
import cv2
import numpy as np
import os
import sys
from datetime import datetime
import time
import argparse
from PIL import ImageGrab, ImageDraw
from win32api import GetSystemMetrics
import win32gui
import win32con

# Get the directory where the executable is located
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    # Running as Python script
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Defaults - use absolute paths
DEFAULT_FOLDER = os.path.join(SCRIPT_DIR, "Recordings")
DEFAULT_DURATION = 50
DEFAULT_FPS = 24
DEFAULT_SLOW_FACTOR = 0.25
SCALE_PERCENT = 70

# Duration presets in seconds
DURATION_PRESETS = {
    "short": 30,
    "medium": 120,
    "long": 300,
    "very-long": 600,
    "ultra-long": 1800
}

# Slow motion presets
SLOW_MOTION_PRESETS = {
    "normal": 1.0,
    "mild": 0.5,
    "slow": 0.25,
    "very-slow": 0.125,
    "ultra-slow": 0.0625
}

# Screen size
screen_width = GetSystemMetrics(0)
screen_height = GetSystemMetrics(1)
scaled_width = int(screen_width * SCALE_PERCENT / 100)
scaled_height = int(screen_height * SCALE_PERCENT / 100)
DEFAULT_RESOLUTION = (scaled_width, scaled_height)

def ensure_folder(path):
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        try:
            os.makedirs(folder)
            print(f"Created directory: {folder}")
        except Exception as e:
            print(f"Error creating directory {folder}: {e}")
            raise

def get_timestamped_filename(folder):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(folder, f"recording_{timestamp}.webm")

def parse_resolution(res_str):
    try:
        width, height = map(int, res_str.lower().split('x'))
        return width, height
    except:
        raise argparse.ArgumentTypeError("Resolution must be in WIDTHxHEIGHT format (e.g. 1280x720)")

def parse_slow_preset(preset):
    if preset in SLOW_MOTION_PRESETS:
        return SLOW_MOTION_PRESETS[preset]
    raise argparse.ArgumentTypeError(f"Unknown preset. Choose from: {', '.join(SLOW_MOTION_PRESETS.keys())}")

def parse_duration_preset(preset):
    if preset in DURATION_PRESETS:
        return DURATION_PRESETS[preset]
    raise argparse.ArgumentTypeError(f"Unknown duration preset. Choose from: {', '.join(DURATION_PRESETS.keys())}")

def get_cursor_position():
    """Get current cursor position"""
    try:
        cursor_pos = win32gui.GetCursorPos()
        return cursor_pos
    except Exception as e:
        print(f"Warning: Could not get cursor position: {e}")
        return None

def draw_cursor_on_image(img, cursor_pos, scale_x, scale_y):
    """Draw cursor on the image with transparent yellow color"""
    if cursor_pos is None:
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    try:
        # Scale cursor position according to image scale
        cursor_x = int(cursor_pos[0] * scale_x)
        cursor_y = int(cursor_pos[1] * scale_y)
        
        # Convert PIL to cv2 format for drawing
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # Create overlay for transparency
        overlay = img_cv.copy()
        
        # Draw transparent yellow cursor (BGR format: Yellow = (0, 255, 255))
        cursor_size = 12
        cv2.circle(overlay, (cursor_x, cursor_y), cursor_size, (0, 255, 255), -1)
        
        # Apply transparency (0.2 = 20% opaque, 80% transparent)
        alpha = 0.2
        img_final = cv2.addWeighted(overlay, alpha, img_cv, 1 - alpha, 0)
        
        return img_final
    except Exception as e:
        print(f"Warning: Could not draw cursor: {e}")
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def record_clip(filename, duration, fps, resolution, slow_factor):
    try:
        ensure_folder(filename)
        
        recording_fps = fps
        output_fps = fps * slow_factor

        # High quality codec settings
        fourcc = cv2.VideoWriter_fourcc(*'VP90')
        out = cv2.VideoWriter(filename, fourcc, output_fps, resolution)
        if not out.isOpened():
            print(f"Error: Could not open video writer for {filename}")
            print(f"Trying alternative codec...")
            # Try alternative codec
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            filename_alt = filename.replace('.webm', '.avi')
            out = cv2.VideoWriter(filename_alt, fourcc, output_fps, resolution)
            if not out.isOpened():
                raise Exception("Could not initialize video writer with any codec")
            filename = filename_alt

        total_frames = int(recording_fps * duration)
        frame_interval = 1.0 / recording_fps
        final_video_duration = duration / slow_factor
        
        # Calculate scale factors for cursor positioning
        scale_x = resolution[0] / screen_width
        scale_y = resolution[1] / screen_height
        
        print(f"Recording clip: {filename}")
        print(f"Recording duration: {duration}s ({duration/60:.1f} minutes)")
        print(f"Total frames to capture: {total_frames}")
        print(f"Recording FPS: {recording_fps}")
        print(f"Output video FPS: {output_fps:.2f}")
        print(f"Final video duration: {final_video_duration:.2f}s ({final_video_duration/60:.1f} minutes)")
        print(f"Slow motion factor: {slow_factor}x")
        print(f"Resolution: {resolution[0]}x{resolution[1]} (Quality: {SCALE_PERCENT}%)")
        print(f"Working directory: {os.getcwd()}")
        print(f"Script directory: {SCRIPT_DIR}")
        
        # Show calculation for user understanding
        if slow_factor < 1.0:
            slowdown_ratio = 1 / slow_factor
            print(f"Note: Video will be {slowdown_ratio:.1f}x slower than real-time")

        start_time = time.time()
        last_progress_time = start_time
        
        for frame_num in range(total_frames):
            frame_start_time = time.time()
            
            try:
                # Capture screen
                img = ImageGrab.grab(bbox=(0, 0, screen_width, screen_height))
                # Use LANCZOS resampling for superior quality resize
                img = img.resize(resolution, resample=3)
                
                # Get cursor position and draw it
                cursor_pos = get_cursor_position()
                img_final = draw_cursor_on_image(img, cursor_pos, scale_x, scale_y)
                
                out.write(img_final)
                
            except Exception as e:
                print(f"Warning: Error capturing frame {frame_num}: {e}")
                continue
            
            # Maintain precise timing
            frame_processing_time = time.time() - frame_start_time
            sleep_time = frame_interval - frame_processing_time
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            # Show progress every second
            if (frame_num + 1) % recording_fps == 0:
                progress = (frame_num + 1) // recording_fps
                current_time = time.time()
                seconds_completed = current_time - start_time
                time_gap = current_time - last_progress_time
                last_progress_time = current_time
                
                print(f"Progress: {progress}/{duration} seconds recorded, completed seconds = {seconds_completed:.2f}s [time gap = {time_gap:.2f}s]")

    except KeyboardInterrupt:
        print("\nRecording stopped by user!")
    except Exception as e:
        print(f"Error during recording: {e}")
        raise
    finally:
        if 'out' in locals():
            out.release()
    
    actual_recording_time = time.time() - start_time
    
    final_video_duration = duration / slow_factor
    
    print(f"\n=== Recording Complete ===")
    print(f"Actual recording time: {actual_recording_time:.2f}s")
    print(f"Expected recording time: {duration}s")
    print(f"Final video duration: {final_video_duration:.2f}s")
    print(f"Slow motion factor: {slow_factor}x")
    print(f"Enhanced Quality: {SCALE_PERCENT}% of original resolution")
    print(f"File saved: {filename}")

def main():
    try:
        parser = argparse.ArgumentParser(description="Screen Recorder with Slow Motion Support")
        parser.add_argument("--output", help="Output path for video file")
        parser.add_argument("--duration", type=int, default=DEFAULT_DURATION, help="Recording duration in seconds")
        parser.add_argument("--duration-preset", type=parse_duration_preset,
                            help=f"Duration preset. Options: {', '.join(DURATION_PRESETS.keys())}")
        parser.add_argument("--fps", type=int, default=DEFAULT_FPS, help="Frames per second to capture")
        parser.add_argument("--resolution", type=parse_resolution, default=DEFAULT_RESOLUTION,
                            help="Output resolution (format: WIDTHxHEIGHT, e.g. 1280x720)")
        parser.add_argument("--slow-factor", type=float, default=DEFAULT_SLOW_FACTOR,
                            help="Slow motion factor (smaller = slower, e.g. 0.25 = 4x slower video)")
        parser.add_argument("--preset", type=parse_slow_preset,
                            help=f"Slow motion preset. Options: {', '.join(SLOW_MOTION_PRESETS.keys())}")

        args = parser.parse_args()
        
        # Duration preset overrides duration
        duration = args.duration_preset if args.duration_preset is not None else args.duration
        
        # If preset is specified, it overrides the slow-factor
        slow_factor = args.preset if args.preset is not None else args.slow_factor
        output_path = args.output or get_timestamped_filename(DEFAULT_FOLDER)

        # Ensure output path is absolute
        if not os.path.isabs(output_path):
            output_path = os.path.abspath(output_path)

        # Show calculation before starting
        final_duration = duration / slow_factor
        print(f"\n=== Recording Plan ===")
        print(f"Input duration: {duration}s ({duration/60:.1f} minutes)")
        print(f"Slow factor: {slow_factor}x")
        print(f"Output video duration: {final_duration:.1f}s ({final_duration/60:.1f} minutes)")
        print(f"File: {output_path}")
        print("=" * 25)

        record_clip(output_path, duration, args.fps, args.resolution, slow_factor)
        
        print("Recording completed successfully")
        return 0
        
    except KeyboardInterrupt:
        print("Recording interrupted by user.")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        cv2.destroyAllWindows()

if __name__ == "__main__":
    sys.exit(main())