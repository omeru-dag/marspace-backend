import cv2
from ultralytics import YOLO
import os

def test():
    model_path = "SunspotSDO_yolo.pt"
    input_video = "sunspot_video.mp4"
    
    print(f"[*] Testing model loading: {model_path}")
    try:
        model = YOLO(model_path)
        print("[+] Model loaded successfully.")
    except Exception as e:
        print(f"[-] Error loading model: {e}")
        return

    print(f"[*] Opening video: {input_video}")
    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        print("[-] Error: Video could not be opened.")
        return
    
    ret, frame = cap.read()
    if not ret:
        print("[-] Error: Could not read first frame.")
        return
    
    print("[+] Successfully read first frame.")
    print(f"[*] Frame shape: {frame.shape}")
    
    print("[*] Running inference on first frame...")
    results = model(frame, verbose=True)
    print(f"[+] Inference complete. Found {len(results[0].boxes)} boxes.")
    
    preview_path = "first_frame_detected.jpg"
    results[0].save(preview_path)
    print(f"[+] Saved detection result to {preview_path}")
    
    cap.release()

if __name__ == "__main__":
    test()
