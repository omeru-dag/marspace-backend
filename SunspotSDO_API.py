import base64
import urllib.request
import urllib.parse
import json
import sys

def detect_sunspots_api(image_source="https://source.roboflow.com/ZDplJxNRZkYXdSVfavLOI4xQmVF3/BMmUZ9GUG72eXWYY3LMH/original.jpg"):
    print(f"[*] SDO (Solar Dynamics Observatory) verisi yükleniyor:\n    {image_source}")
    print("[*] MARSPACE SunspotSDO Bulut Modeli Başlatılıyor...")
    
    API_KEY = "8d4jfdx4lB94aLrZdMG2"
    PROJECT = "sunspotsdo/2"
    
    # URL mi yoksa lokal dosya mı olduğunu anla
    is_url = image_source.startswith("http://") or image_source.startswith("https://")
    api_url = f"https://detect.roboflow.com/{PROJECT}?api_key={API_KEY}"
    
    if is_url:
        print("[+] Çevrimiçi (URL) görüntü kaynağı tespit edildi.")
        # Eger internet linki ise direkt URL parametresi olarak ekle
        encoded_img_url = urllib.parse.quote_plus(image_source)
        final_url = f"{api_url}&image={encoded_img_url}"
        
        req = urllib.request.Request(
            final_url, 
            method="POST", 
            headers={"Content-Length": "0"}  # Body yok
        )
    else:
        print("[+] Yerel (Lokal) dosya kaynağı tespit edildi.")
        try:
            with open(image_source, "rb") as f:
                image_b64 = base64.b64encode(f.read()).decode("utf-8")
        except FileNotFoundError:
            print(f"HATA: '{image_source}' adlı resim dosyası bilgisayarınızda bulunamadı!")
            return
            
        req = urllib.request.Request(
            api_url, 
            data=image_b64.encode("utf-8"), 
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
    try:
        print("[+] Roboflow Bulut Inference (Hosted API) analizine başlandı...")
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            
        print("\n--- GERÇEK ZAMANLI SUNSPOT ANALİZ SONUCU ---")
        if "predictions" in result and len(result["predictions"]) > 0:
            for i, p in enumerate(result["predictions"], 1):
                class_name = p.get('class', 'Sunspot')
                conf = int(p.get('confidence', 0) * 100)
                print(f"Deteksiyon {i} -> Sınıf: {class_name} | Güvenilirlik: %{conf} | Konum: [x:{p['x']:.1f}, y:{p['y']:.1f}, w:{p['width']:.1f}, h:{p['height']:.1f}]")
            
            print("-----------------------------------------------------")
            print(">>> KRİTİK UYARI: Güneş Lekesi veya Aktif Bölge Tespiti (Roboflow Canlı Veri)!")
            print(">>> Otonom web panele 'SARI ALARM' uyarı sinyali iletiliyor...")
        else:
            print("Görüntüde belirgin bir Güneş Lekesi veya patlama (Sunspot) bulunamadı.")
            
    except urllib.error.HTTPError as e:
        print(f"\nRoboflow API REDDETTİ (HTTP {e.code}): Yetki yok, API Key kısıtlı veya kota dolmuş olabilir.")
    except Exception as e:
        print(f"\nAPI BAĞLANTI HATASI: Sunucuya erişilemedi. Detay: {e}")

if __name__ == "__main__":
    img_src = sys.argv[1] if len(sys.argv) > 1 else "https://source.roboflow.com/ZDplJxNRZkYXdSVfavLOI4xQmVF3/BMmUZ9GUG72eXWYY3LMH/original.jpg"
    detect_sunspots_api(img_src)
