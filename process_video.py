import cv2
from ultralytics import YOLO
import os
import sys

def process_video(input_path, output_path, model_path="SunspotSDO_yolo.pt"):
    print(f"[*] YOLOv8 Modeli Yukleniyor: {model_path}", flush=True)
    try:
        model = YOLO(model_path)
    except Exception as e:
        print(f"[-] Hata: Model yuklenemedi: {e}", flush=True)
        return
    
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"[-] Hata: Video dosyasi acilamadi: {input_path}", flush=True)
        return

    # Video parametrelerini al
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0: fps = 24

    # Output video writer - mp4v yerine XVID veya mp4v deneyelim
    # fourcc = cv2.VideoWriter_fourcc(*'XVID')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Standart Windows/macOS destegi
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print(f"[*] Video Islaniyor: {input_path} -> {output_path}", flush=True)
    print(f"[*] Cozunurluk: {width}x{height}, FPS: {fps}", flush=True)

    frame_count = 0
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # YOLOv8 ile tahmin yap
            results = model(frame, verbose=False)
            
            # Tahminleri cerceve uzerine ciz
            annotated_frame = results[0].plot()
            
            # Kareyi yaz
            out.write(annotated_frame)
            
            frame_count += 1
            if frame_count % 30 == 0:
                print(f"[*] ISLENEN KARE: {frame_count}", flush=True)
                # stdout'u zorla bosalt
                sys.stdout.flush()

    except Exception as e:
        print(f"[-] Hata: Islem sirasinda hata olustu: {e}", flush=True)
    finally:
        cap.release()
        out.release()
        print(f"[+] ISLEM TAMAMLANDI! Toplam {frame_count} kare islendi.", flush=True)
        print(f"[+] Cikti Dosyasi: {os.path.abspath(output_path)}", flush=True)

if __name__ == "__main__":
    input_video = "sunspot_video.mp4"
    output_video = "sunspot_video_processed.mp4"
    
    if os.path.exists(input_video):
        process_video(input_video, output_video)
    else:
        print(f"[-] Hata: Giris videosu {input_video} bulunamadi.", flush=True)
