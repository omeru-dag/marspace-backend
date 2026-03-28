import http.server
import socketserver
import cv2
import time
import subprocess
import json
import base64
import urllib.request
import sys
import threading

PORT = 5006
YOUTUBE_URL = "https://www.youtube.com/watch?v=NA961oOs2FY"
START_SECONDS = 11

API_KEY = "8d4jfdx4lB94aLrZdMG2"
PROJECT_ID = "sunspot-detection-using-yolov5"
VERSION = "5"
API_URL = f"https://detect.roboflow.com/{PROJECT_ID}/{VERSION}?api_key={API_KEY}"

# ---- YouTube URL coz ----
def resolve_url():
    print(f"[*] yt-dlp ile video linki cozuluyor...")
    r = subprocess.run(
        [sys.executable, '-m', 'yt_dlp', '-g', '-f', 'best[ext=mp4]/best', YOUTUBE_URL],
        capture_output=True, text=True
    )
    if r.returncode == 0:
        url = r.stdout.strip().split('\n')[0]
        print("[+] Video linki cozuldu.")
        return url
    print(f"[!] yt-dlp hata: {r.stderr[:200]}")
    return None

print("[*] Baslatiyor...")
STREAM_URL = resolve_url()

# ---- Roboflow API (arka plan) ----
last_preds = []
pred_lock = threading.Lock()

def call_api(frame):
    global last_preds
    try:
        small = cv2.resize(frame, (480, 640))
        _, buf = cv2.imencode('.jpg', small)
        b64 = base64.b64encode(buf).decode("utf-8")
        req = urllib.request.Request(
            API_URL, data=b64.encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            with pred_lock:
                last_preds = result.get("predictions", [])
    except Exception:
        pass

# ---- MJPEG Stream ----

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path != '/stream':
            self.send_response(404)
            self.end_headers()
            return

        if not STREAM_URL:
            self.send_error(503)
            return

        # Baslik gonder
        self.send_response(200)
        self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frameboundary')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()

        cap = cv2.VideoCapture(STREAM_URL)
        if not cap.isOpened():
            print("[!] Video acilamadi!")
            return

        # Ilk 11 saniyeyi atla
        vid_fps = cap.get(cv2.CAP_PROP_FPS) or 24
        skip = int(START_SECONDS * vid_fps)
        print(f"[*] {skip} frame atlaniyor ({START_SECONDS}s, fps={vid_fps})...")
        for _ in range(skip):
            cap.read()
        print(f"[*] Stream baslatildi!")

        interval = 1.0 / 24.0
        idx = 0
        api_busy = False

        try:
            while True:
                t0 = time.time()
                ok, frame = cap.read()
                if not ok:
                    break

                out = cv2.resize(frame, (480, 640))

                if idx % 15 == 0 and not api_busy:
                    api_busy = True
                    def _run(f):
                        nonlocal api_busy
                        call_api(f)
                        api_busy = False
                    threading.Thread(target=_run, args=(frame.copy(),), daemon=True).start()
                idx += 1

                with pred_lock:
                    preds = list(last_preds)
                for p in preds:
                    cx, cy = int(p['x']), int(p['y'])
                    pw, ph = int(p['width']), int(p['height'])
                    x1, y1 = cx - pw // 2, cy - ph // 2
                    x2, y2 = cx + pw // 2, cy + ph // 2
                    lbl = f"{p.get('class','?')} {p.get('confidence',0):.2f}"
                    cv2.rectangle(out, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(out, lbl, (x1, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)

                cv2.putText(out, "SunspotSDO CANLI ANALIZ", (10, 22),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                _, jpg = cv2.imencode('.jpg', out, [cv2.IMWRITE_JPEG_QUALITY, 85])
                data = jpg.tobytes()

                try:
                    self.wfile.write(b'--frameboundary\r\n')
                    self.wfile.write(b'Content-Type: image/jpeg\r\n')
                    self.wfile.write(f'Content-Length: {len(data)}\r\n\r\n'.encode())
                    self.wfile.write(data)
                    self.wfile.write(b'\r\n')
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
                    break

                dt = time.time() - t0
                if dt < interval:
                    time.sleep(interval - dt)
        except Exception as e:
            print(f"[!] Hata: {e}")
        finally:
            cap.release()
            print("[*] Stream sonlandi.")

class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

if __name__ == '__main__':
    server = Server(('', PORT), Handler)
    print(f"[*] SunspotSDO Stream: http://localhost:{PORT}/stream")
    server.serve_forever()
