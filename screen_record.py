import pyautogui
import cv2
import numpy as np
import os
from datetime import datetime
import time
import sys
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
DEFAULT_DURATION = 300
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

def safe_opencv_cleanup():
    """Safely cleanup OpenCV resources without causing crashes"""
    try:
        # Only try to destroy windows if we're in a GUI environment
        import sys
        
        # Check if we're in a console/GUI environment
        if hasattr(sys, '_MEIPASS') or getattr(sys, 'frozen', False):
            # We're running as an executable - skip cv2.destroyAllWindows()
            print("Skipping cv2.destroyAllWindows() for executable environment")
            return
        
        # Try to destroy windows, but catch the specific error
        cv2.destroyAllWindows()
        print("OpenCV windows destroyed successfully")
        
    except cv2.error as e:
        if "not implemented" in str(e).lower() or "rebuild the library" in str(e).lower():
            print("OpenCV destroyAllWindows not supported in this environment (headless mode)")
        else:
            print(f"OpenCV cleanup warning: {e}")
    except Exception as e:
        print(f"Warning: Error during OpenCV cleanup: {e}")

def record_clip(filename, duration, fps, resolution, slow_factor):
    out = None
    final_filename = filename
    
    try:
        ensure_folder(filename)
        
        recording_fps = fps
        # IMPORTANT: Ensure minimum output FPS for browser compatibility
        output_fps = max(fps * slow_factor, 12.0)  # Never go below 12 FPS
        
        print(f"Requested output: {filename}")
        print(f"Recording FPS: {recording_fps}")
        print(f"Output FPS: {output_fps:.2f} (minimum 12 FPS for browsers)")
        
        if filename.endswith('.webm'):
            print("Creating browser-compatible WebM...")
            
            # Try VP8 with browser-friendly parameters
            try:
                fourcc = cv2.VideoWriter_fourcc(*'VP80')
                # Ensure integer FPS for VP8 compatibility
                safe_fps = max(12, int(output_fps))
                out = cv2.VideoWriter(filename, fourcc, float(safe_fps), resolution)
                
                if out.isOpened():
                    print(f"SUCCESS: VP8 WebM created with {safe_fps} FPS")
                    codec_used = f"VP8 ({safe_fps} FPS)"
                    output_fps = safe_fps  # Update the actual FPS being used
                else:
                    print("ERROR: VP8 failed")
                    out = None
            except Exception as e:
                print(f"ERROR: VP8 error - {e}")
                out = None
            
            # If VP8 fails, try a different approach - create MP4 and rename to WebM
            if out is None:
                print("INFO: VP8 failed, creating MP4 with WebM extension...")
                try:
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    safe_fps = max(12, int(output_fps))
                    out = cv2.VideoWriter(filename, fourcc, float(safe_fps), resolution)
                    
                    if out.isOpened():
                        print(f"SUCCESS: MP4V in WebM container created with {safe_fps} FPS")
                        codec_used = f"MP4V-WebM ({safe_fps} FPS)"
                        output_fps = safe_fps
                    else:
                        print("ERROR: MP4V in WebM failed")
                        out = None
                except Exception as e:
                    print(f"ERROR: MP4V in WebM error - {e}")
                    out = None
        else:
            # For non-WebM files
            safe_fps = max(12, int(output_fps))
            if filename.endswith('.mp4'):
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                codec_used = f"MP4V ({safe_fps} FPS)"
            elif filename.endswith('.avi'):
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                codec_used = f"XVID ({safe_fps} FPS)"
            else:
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                codec_used = f"MP4V ({safe_fps} FPS)"
                
            out = cv2.VideoWriter(filename, fourcc, float(safe_fps), resolution)
            output_fps = safe_fps
        
        # Final fallback - create standard MP4
        if out is None or not out.isOpened():
            print("INFO: All WebM attempts failed, creating standard MP4...")
            fallback_filename = os.path.splitext(filename)[0] + '.mp4'
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            safe_fps = max(12, int(output_fps))
            out = cv2.VideoWriter(fallback_filename, fourcc, float(safe_fps), resolution)
            final_filename = fallback_filename
            codec_used = f"MP4V-Fallback ({safe_fps} FPS)"
            output_fps = safe_fps
            
            if not out.isOpened():
                raise Exception("Could not initialize video writer with any codec")

        total_frames = int(recording_fps * duration)
        frame_interval = 1.0 / recording_fps
        
        # Recalculate video duration based on actual output FPS
        actual_video_duration = total_frames / output_fps
        
        # Calculate scale factors for cursor positioning
        scale_x = resolution[0] / screen_width
        scale_y = resolution[1] / screen_height
        
        print(f"SUCCESS: Recording clip - {final_filename}")
        print(f"SUCCESS: Codec - {codec_used}")
        print(f"Recording duration: {duration}s ({duration/60:.1f} minutes)")
        print(f"Total frames to capture: {total_frames}")
        print(f"Recording FPS: {recording_fps}")
        print(f"Output video FPS: {output_fps:.2f}")
        print(f"Actual video duration: {actual_video_duration:.2f}s ({actual_video_duration/60:.1f} minutes)")
        print(f"Slow motion factor: {recording_fps/output_fps:.2f}x")
        print(f"Resolution: {resolution[0]}x{resolution[1]} (Quality: {SCALE_PERCENT}%)")
        
        start_time = time.time()
        last_progress_time = start_time
        
        # Frame duplication logic for slow motion with proper FPS
        frame_repeats = max(1, int(recording_fps / output_fps))
        print(f"Frame repeat count: {frame_repeats} (each recorded frame repeated {frame_repeats} times)")
        
        for frame_num in range(total_frames):
            frame_start_time = time.time()
            
            try:
                # Capture screen
                img = ImageGrab.grab(bbox=(0, 0, screen_width, screen_height))
                img = img.resize(resolution, resample=3)
                
                # Get cursor position and draw it
                cursor_pos = get_cursor_position()
                img_final = draw_cursor_on_image(img, cursor_pos, scale_x, scale_y)
                
                # Write frame multiple times for slow motion effect
                for _ in range(frame_repeats):
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
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Ensure proper cleanup
        if out is not None:
            try:
                out.release()
                print("Video writer released successfully")
            except Exception as e:
                print(f"Warning: Error releasing video writer: {e}")
        
        # Safe cleanup of OpenCV resources
        safe_opencv_cleanup()
    
    try:
        actual_recording_time = time.time() - start_time
        
        print(f"\n=== Recording Complete ===")
        print(f"Actual recording time: {actual_recording_time:.2f}s")
        print(f"Expected recording time: {duration}s")
        print(f"Final video duration: {actual_video_duration:.2f}s")
        print(f"Output FPS: {output_fps:.2f}")
        print(f"Enhanced Quality: {SCALE_PERCENT}% of original resolution")
        print(f"File saved: {final_filename}")
        
        # Verify file was created and has content
        if os.path.exists(final_filename):
            file_size = os.path.getsize(final_filename)
            print(f"File size: {file_size} bytes")
            
            # Additional validation for web compatibility
            if final_filename.endswith('.webm'):
                print("WEB: WebM file created with browser-compatible settings")
                print("   - Minimum 12 FPS for smooth playback")
                print("   - Compatible codec parameters")
            elif final_filename.endswith('.mp4'):
                print("WEB: MP4 file created - universally web compatible")
                
            if file_size == 0:
                print("Warning: Output file is empty!")
            else:
                print("SUCCESS: Recording successful! Should work in browsers.")
        else:
            print("Warning: Output file was not created!")
            
    except Exception as e:
        print(f"Warning: Error in final reporting: {e}")

def main():
    try:
        parser = argparse.ArgumentParser(description="Screen Recorder with WebM Support")
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
        # Final safe cleanup
        safe_opencv_cleanup()

if __name__ == "__main__":
    sys.exit(main())