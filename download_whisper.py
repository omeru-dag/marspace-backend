import urllib.request
import zipfile
import os
import json
import shutil

def download_latest_whisper():
    print("En güncel whisper.cpp sürümü bulunuyor...")
    req = urllib.request.Request("https://api.github.com/repos/ggerganov/whisper.cpp/releases/latest", headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"Hata: API isteği başarısız oldu: {e}")
        return
        
    download_url = None
    for asset in data.get("assets", []):
        if "bin-x64.zip" in asset["name"]: # Windows x64 binaries
            download_url = asset["browser_download_url"]
            print(f"Sürüm bulundu: {asset['name']}")
            break
            
    if not download_url:
        print("Windows x64 sürümü bulunamadı!")
        return

    print(f"İndiriliyor: {download_url}")
    zip_path = "whisper_temp.zip"
    try:
        urllib.request.urlretrieve(download_url, zip_path)
    except Exception as e:
        print(f"Hata: İndirme başarısız oldu: {e}")
        return
        
    out_dir = "whisper_bin"
    # Eğer Release klasörü varsa, orayı temizleyip kuralım veya direkt oraya kuralım
    release_dir = os.path.join(out_dir, "Release")
    os.makedirs(release_dir, exist_ok=True)
    
    print("Zip arşivi çıkarılıyor...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # zip içerisindeki dosyaları listeleyelim
            for file_info in zip_ref.infolist():
                # Bazen iç içe klasör içinde olabilir, ana dosya isimlerini alıp direkt Release klasörüne atalım
                filename = os.path.basename(file_info.filename)
                if filename:
                    source = zip_ref.open(file_info)
                    target = open(os.path.join(release_dir, filename), "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)
    except Exception as e:
        print(f"Hata: Çıkarma işlemi başarısız oldu: {e}")
        return
        
    os.remove(zip_path)
    
    # ggml-base.bin modelini indir
    model_path = os.path.join(release_dir, "ggml-base.bin")
    if not os.path.exists(model_path):
        print("Whisper ggml-base.bin modeli indiriliyor...")
        model_url = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin"
        try:
            urllib.request.urlretrieve(model_url, model_path)
            print("Model indirme tamamlandı.")
        except Exception as e:
            print(f"Model indirilirken hata oluştu: {e}")
    else:
        print("Model dosyası zaten mevcut.")
        
    print("Kurulum başarılı!")

if __name__ == "__main__":
    download_latest_whisper()
