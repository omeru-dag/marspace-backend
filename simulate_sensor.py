import time
import urllib.request
import urllib.parse
import sys

# MARSPACE Otonom Senaryo Faz Kontrolcüsü (Eski rastgele sensör testi iptal edildi)
BASE_URL = "http://localhost:5500"

def send_val(path, val):
    try:
        url = f"{BASE_URL}{path}{urllib.parse.quote(str(val))}"
        urllib.request.urlopen(url)
    except Exception as e:
        # Proxy kapalı olabilir, sessizce devam et
        pass

def trigger_phase(phase):
    print(f"\n[*] FAZ {phase} Senaryosu Gönderiliyor...")
    send_val("/set_phase?val=", phase)
    
    # Arka plandaki verileri de faza uygun şekilde statik olarak güncelliyoruz.
    if phase == 1:
        send_val("/set_wind?val=", 700)
        send_val("/set_kp?val=", 6.0)
        send_val("/set_bz?val=", -10)
        send_val("/set_gic_amp?val=", 0.5)
        send_val("/set_freq?val=", 50.00)
    elif phase == 2:
        send_val("/set_wind?val=", 1600)
        send_val("/set_kp?val=", 8.5)
        send_val("/set_bz?val=", -30)
        send_val("/set_gic_amp?val=", 85)
        send_val("/set_freq?val=", 49.82)
    elif phase == 3:
        send_val("/set_wind?val=", 1850)
        send_val("/set_kp?val=", 9.5)
        send_val("/set_bz?val=", -50)
        send_val("/set_gic_amp?val=", 150)
        send_val("/set_freq?val=", 49.72)
    elif phase == 4:
        send_val("/set_wind?val=", 400)
        send_val("/set_kp?val=", 3.0)
        send_val("/set_bz?val=", 2.0)
        send_val("/set_gic_amp?val=", 0.5)
        send_val("/set_freq?val=", 50.00)

    print("[+] Arayüze tetikleme yapıldı. (Animasyonlar Front-End üzerinden işlenecek)")

def main():
    print("=========================================================")
    print("MARSPACE SCADA - OTONOM SENARYO VE FAZ KONTROLCÜSÜ")
    print("NOT: Eski rastgele veri üreten test iptal edilmiştir.")
    print("Arayüz animasyonları ile tam senkronize kontrol sağlar.")
    print("=========================================================")
    print("1: FAZ 1 (UYDULAR GÜVENLİ MODA)")
    print("2: FAZ 2 (METROLAR TAHLİYE & KRİTİK HARİCİ KESİNTİ)")
    print("3: FAZ 3 (ŞEBEKELER KORUMA MODU AKTİF)")
    print("4: FAZ 4 (SİSTEMİN YAVAŞÇA AKTİF EDİLMESİ)")
    print("0: Çıkış")
    print("=========================================================")
    
    while True:
        try:
            cmd = input("\nLütfen Tetiklemek İstediğiniz Fazı Seçin (1-4): ")
            if cmd == '0':
                print("Çıkılıyor...")
                sys.exit(0)
            if cmd in ['1', '2', '3', '4']:
                trigger_phase(int(cmd))
            else:
                print("Geçersiz seçim. Sadece 1, 2, 3 veya 4 girebilirsiniz.")
        except KeyboardInterrupt:
            print("\nÇıkılıyor...")
            sys.exit(0)

if __name__ == "__main__":
    main()
