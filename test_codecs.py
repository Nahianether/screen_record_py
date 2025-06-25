import cv2
import numpy as np
import os

def test_codec_support():
    print("Testing OpenCV codec support...")
    print(f"OpenCV version: {cv2.__version__}")
    
    # Create a test frame
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    test_frame[:] = (255, 0, 0)  # Blue frame
    
    codecs_to_test = [
        ('VP80', 'VP8', '.webm'),
        ('VP90', 'VP9', '.webm'),
        ('mp4v', 'MP4V', '.mp4'),
        ('XVID', 'XVID', '.avi'),
        ('H264', 'H264', '.mp4'),
        ('avc1', 'AVC1', '.mp4'),
    ]
    
    working_codecs = []
    
    for fourcc_str, name, ext in codecs_to_test:
        try:
            fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
            filename = f'test_{name.lower()}{ext}'
            
            # Test if VideoWriter can be opened
            writer = cv2.VideoWriter(filename, fourcc, 1.0, (640, 480))
            
            if writer.isOpened():
                # Try to write a frame
                writer.write(test_frame)
                writer.release()
                
                # Check if file was created and has content
                if os.path.exists(filename):
                    size = os.path.getsize(filename)
                    if size > 0:
                        print(f"✅ {name} ({fourcc_str}) - WORKS ({size} bytes)")
                        working_codecs.append((fourcc_str, name, ext))
                        os.remove(filename)  # Clean up
                    else:
                        print(f"❌ {name} ({fourcc_str}) - File created but empty")
                        os.remove(filename)
                else:
                    print(f"❌ {name} ({fourcc_str}) - No file created")
            else:
                print(f"❌ {name} ({fourcc_str}) - Cannot open VideoWriter")
                if writer:
                    writer.release()
                    
        except Exception as e:
            print(f"❌ {name} ({fourcc_str}) - Error: {e}")
    
    print(f"\n=== Summary ===")
    if working_codecs:
        print("Working codecs:")
        for fourcc_str, name, ext in working_codecs:
            print(f"  - {name} ({fourcc_str}) for {ext} files")
    else:
        print("❌ No working codecs found!")
    
    return working_codecs

if __name__ == "__main__":
    test_codec_support()