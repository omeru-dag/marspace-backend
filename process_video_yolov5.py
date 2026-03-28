import cv2
import base64
import json
import urllib.request
import time
import os
import sys
from concurrent.futures import ThreadPoolExecutor

# Roboflow Config (Kullanicinin belirttigi model)
API_KEY = "8d4jfdx4lB94aLrZdMG2"
WORKSPACE = "internship-projects"
PROJECT_ID = "sunspot-detection-using-yolov5"
VERSION = "5" # roboflow_youtube_stream.py'den alindi
API_URL = f"https://detect.roboflow.com/{PROJECT_ID}/{VERSION}?api_key={API_KEY}"

def call_roboflow_api(frame):
    try:
        # Roboflow YOLOv5 icin genelde 640x640 idealdir
        _, buf = cv2.imencode('.jpg', frame)
        b64 = base64.b64encode(buf).decode("utf-8")
        req = urllib.request.Request(
            API_URL, data=b64.encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("predictions", [])
    except Exception:
        return []

def process_video_final_choice(input_path, output_path, max_workers=10):
    print(f"[*] Roboflow YOLOv5 (internship-projects) Isleme Basladi.", flush=True)
    print(f"[*] Model: {PROJECT_ID} v{VERSION}", flush=True)
    
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"[-] Hata: {input_path} acilamadi.", flush=True)
        return

    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0: fps = 24

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    frame_count = 0
    last_predictions = []
    chunk_size = 150 # Sitedeki 15-frame interval mantigi ile 10 API call/chunk
    
    try:
        while cap.isOpened():
            chunk_frames = []
            for _ in range(chunk_size):
                ret, frame = cap.read()
                if not ret:
                    break
                chunk_frames.append(frame)
            
            if not chunk_frames:
                break
            
            # API'ye gidecek kareleri sec (15'er ara ile)
            api_frames_indices = [i for i in range(len(chunk_frames)) if (frame_count + i) % 15 == 0]
            api_frames = [chunk_frames[idx] for idx in api_frames_indices]
            
            # Paralel API Cagrilari
            if api_frames:
                with ThreadPoolExecutor(max_workers=len(api_frames)) as executor:
                    new_predictions = list(executor.map(call_roboflow_api, api_frames))
                api_map = {idx: pred for idx, pred in zip(api_frames_indices, new_predictions)}
            else:
                api_map = {}

            # Kareleri Isle ve Yaz
            for i, frame in enumerate(chunk_frames):
                if i in api_map:
                    last_predictions = api_map[i]
                
                annotated_frame = frame.copy()
                for p in last_predictions:
                    cx, cy = int(p['x']), int(p['y'])
                    pw, ph = int(p['width']), int(p['height'])
                    x1, y1 = cx - pw // 2, cy - ph // 2
                    x2, y2 = cx + pw // 2, cy + ph // 2
                    lbl = f"{p.get('class','?')} {p.get('confidence',0):.2f}"
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(annotated_frame, lbl, (x1, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)

                cv2.putText(annotated_frame, f"MARSPACE Roboflow YOLOv5 ({PROJECT_ID})", (20, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                out.write(annotated_frame)
            
            frame_count += len(chunk_frames)
            print(f"[*] ISLENEN TOPLAM KARE: {frame_count} / 88262", flush=True)
            sys.stdout.flush()

    except Exception as e:
        print(f"[-] Hata: {e}", flush=True)
    finally:
        cap.release()
        out.release()
        print(f"[+] ISLEM TAMAMLANDI! Cikti: {output_path}", flush=True)

if __name__ == "__main__":
    input_video = "sunspot_video.mp4"
    output_video = "sunspot_video_yolov5_processed.mp4"
    if os.path.exists(input_video):
        process_video_final_choice(input_video, output_video)
    else:
        print(f"[-] Hata: {input_video} yok.")
