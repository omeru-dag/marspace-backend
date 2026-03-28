import random
import time
import urllib.request

# Sensorsimulator: 600 - 1800 arasi veri uretir
PROXY_URL = "http://localhost:5500/set_wind?val="
GIC_URL = "http://localhost:5500/set_gic?val="
KP_URL = "http://localhost:5500/set_kp?val="
BZ_URL = "http://localhost:5500/set_bz?val="

def simulate():
    print("[*] Solar Wind Sensor Simulation started.")
    print("[*] Target: http://localhost:5500")
    
    try:
        while True:
            # 600 - 1800 arasi rastgele veri
            val_wind = random.randint(600, 1800)
            val_gic = round(random.uniform(0.1, 25.0), 2)
            val_kp = round(random.uniform(0.0, 9.0), 1)
            val_bz = round(random.uniform(-40.0, 10.0), 1)
            
            print(f"[>] Sending telemetry: Wind={val_wind}, GIC={val_gic}, Kp={val_kp}, Bz={val_bz}")
            
            try:
                urllib.request.urlopen(PROXY_URL + str(val_wind))
                urllib.request.urlopen(GIC_URL + str(val_gic))
                urllib.request.urlopen(KP_URL + str(val_kp))
                urllib.request.urlopen(BZ_URL + str(val_bz))
            except Exception as e:
                print(f"[!] Warning: Could not connect to proxy. Is it running? ({e})")
            
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n[*] Simulation stopped.")

if __name__ == "__main__":
    simulate()
