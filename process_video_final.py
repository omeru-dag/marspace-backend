from ultralytics import YOLO
import os
import shutil

def process_video_official(input_path, model_path="SunspotSDO_yolo.pt"):
    print(f"[*] YOLOv8 Otonom Isleme Basladi: {model_path}", flush=True)
    if not os.path.exists(input_path):
        print(f"[-] Hata: {input_path} bulunamadi.")
        return

    model = YOLO(model_path)
    
    # Ultralytics'in en hizli video isleme metodu:
    print(f"[*] Ultralytics Predict motoru calistiriliyor... {input_path}", flush=True)
    
    # source: video dosyasi
    # save: sonuclari kaydet
    # project/name: nereye kaydedecegi
    results = model.predict(
        source=input_path, 
        save=True, 
        project="marspace_runs", 
        name="video_analysis", 
        exist_ok=True,
        device="cpu" # GPU varsa GPU kullanir ama CPU garantidir
    )
    
    print(f"[+] Isleme tamamlandi. Sonuclar 'marspace_runs/video_analysis' icinde kaydedildi.", flush=True)

if __name__ == "__main__":
    input_video = "sunspot_video.mp4"
    process_video_official(input_video)
