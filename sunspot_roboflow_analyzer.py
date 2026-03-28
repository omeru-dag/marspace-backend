from roboflow import Roboflow
import sys

# KULLANIM:
# 1. roboflow kütüphanesini kurun: pip install roboflow
# 2. Aşağıdaki api_key alanına kendi Roboflow Private API Key'inizi yapıştırın
# 3. python sunspot_roboflow_analyzer.py sdo_resmi.jpg

def analyze_sunspot_with_roboflow(image_path, api_key="BURAYA_API_KEY_YAZIN"):
    if api_key == "BURAYA_API_KEY_YAZIN":
        print("HATA: Lütfen Roboflow hesabınızdan aldığınız API Anahtarını koda ekleyin!")
        print("Bkz: https://docs.roboflow.com/api-reference/authentication")
        return

    print("[*] Roboflow Sunspot Detection YOLOv5 Modeline Bağlanılıyor...")
    try:
        rf = Roboflow(api_key=api_key)
        # Gönderdiğiniz linkteki "internship-projects" çalışma alanından modeli çekiyoruz
        project = rf.workspace("internship-projects").project("sunspot-detection-using-yolov5")
        
        # En güncel eğitilmiş versiyonu (genelde 1 veya 2'dir) seçiyoruz
        model = project.version(1).model
        
        print(f"[*] {image_path} resmi analiz ediliyor...")
        
        # Bulut (Hosted) Inferance üzerinden veya lokal model üzerinden tahmini al
        prediction = model.predict(image_path, confidence=40, overlap=30).json()
        
        print("\n--- ROBOFLOW YOLOv5 ANALİZ SONUCU ---")
        if "predictions" in prediction and len(prediction["predictions"]) > 0:
            for i, p in enumerate(prediction["predictions"], 1):
                print(f"Leke {i} -> Sınıf: {p['class']} | Güvenilirlik: %{int(p['confidence']*100)} | Konum: [x:{p['x']}, y:{p['y']}]")
        else:
            print("Bu görüntüde herhangi bir Güneş Lekesi (Sunspot) tespit edilemedi.")
            
    except Exception as e:
        print(f"Roboflow API Hatası: {e}")

if __name__ == "__main__":
    img = sys.argv[1] if len(sys.argv) > 1 else "gunes_resmi.jpg"
    analyze_sunspot_with_roboflow(img)
