import urllib.request
import json
import zipfile
import os
import sys
import subprocess

def download_and_test():
    print("[*] Zenodo Bilimsel Veritabanından SunspotsYoloDataset (DOI: 10.5281/zenodo.11441091) sorgulanıyor...")
    url = "https://zenodo.org/api/records/11441091"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Hata: Zenodo API'sine ulaşılamadı. ({e})")
        return

    # Sadece .zip uzantılı asıl veri setini bul
    zip_url = None
    file_info = None
    for f in data.get('files', []):
        if f['key'].endswith('.zip'):
            zip_url = f['links']['self']
            file_info = f
            break

    if not zip_url:
        print("HATA: Kayıtta ZIP dosyası bulunamadı.")
        return

    mb_size = int(file_info.get('size', 0)) / (1024 * 1024)
    print(f"[+] Veriseti ZIP linki bulundu: {file_info['key']} ({mb_size:.1f} MB)")

    zip_path = "SunspotsYoloDataset_V2.zip"
    if os.path.exists(zip_path):
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                # Test the zip integrity
                if z.testzip() is not None:
                    raise Exception("Corrupt file in zip")
            print("[+] ZIP dosyası bilgisayarda zaten mevcut ve BAŞARIYLA DOĞRULANDI.")
        except Exception:
            print("[-] Mevcut ZIP dosyası bozuk veya indirilirken yarım kesilmiş!")
            print("[*] Bozuk dosya silinip baştan sağlıklı şekilde indiriliyor...")
            os.remove(zip_path)

    if not os.path.exists(zip_path):
        print(f"[*] Büyük Dataset ({mb_size:.1f} MB) İndiriliyor...")
        print("[!] LÜTFEN BEKLEYİN - Bu işlem internet hızınıza bağlı olarak birkaç dakika sürebilir.")
        
        # Dosya indirilirken gelişimi göstermek için
        def reporthook(count, block_size, total_size):
            downloaded = count * block_size
            percent = downloaded * 100 / total_size if total_size > 0 else 0
            # Sadece her %5'lik artışta yazdırarak terminalin kirlenmesini önle
            if int(percent) % 5 == 0 and int(percent) > 0:
                sys.stdout.write(f"\r[~] İndirme İlerlemesi: %{int(percent)} ({downloaded/(1024*1024):.1f} MB / {total_size/(1024*1024):.1f} MB)")
                sys.stdout.flush()

        urllib.request.urlretrieve(zip_url, zip_path, reporthook=reporthook)
        print("\n[+] İndirme BÜTÜNÜYLE tamamlandı!")

    print("[*] ZIP içerisinden örnek bir güneş fotoğrafı çıkartılıyor...")
    test_image = None
    extract_folder = "Sunspot_Test_Images"
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            # zip içerisindeki ilk .jpg dosyasını bul ve çıkar
            for info in z.infolist():
                if info.filename.lower().endswith('.jpg') and "__MACOSX" not in info.filename:
                    z.extract(info, extract_folder)
                    test_image = os.path.join(extract_folder, info.filename)
                    print(f"[+] Test görseli başarıyla çıkarıldı: {test_image}")
                    break
    except Exception as e:
        print(f"Hata: ZIP açılamadı. ({e})")
        return

    if test_image:
        print("\n" + "="*50)
        print("🚀 OTONOM MODEL TESTİ (ROBOFLOW) BAŞLATILIYOR")
        print("="*50)
        # Sizin Roboflow Hosted API modelinizi (SunspotSDO_API.py) çalıştır
        subprocess.run([sys.executable, "SunspotSDO_API.py", test_image])
        
if __name__ == "__main__":
    download_and_test()
