import http.server
import socketserver
import cv2
import os
import time
import subprocess
import sys
from ultralytics import YOLO

PORT = 5002
YOUTUBE_URL = "https://www.youtube.com/watch?v=NA961oOs2FY"
MODEL_PATH = "SunspotSDO_yolo.pt"

print(f"[*] YOLO modeli yükleniyor: {MODEL_PATH}")
try:
    model = YOLO(MODEL_PATH)
    print(f"[*] Model yüklendi.")
except Exception as e:
    print(f"Hata: YOLO modeli yüklenemedi: {e}")
    model = None

def get_youtube_stream_url(url):
    try:
        print(f"[*] yt-dlp ile çözünürlük linki alınıyor... {url}")
        # Use python -m yt_dlp to bypass PATH issues
        result = subprocess.run(
            [sys.executable, '-m', 'yt_dlp', '-g', '-f', 'best[ext=mp4]/best', url],
            capture_output=True, text=True, check=True
        )
        stream_url = result.stdout.strip().split('\n')[0]
        return stream_url
    except subprocess.CalledProcessError as e:
        print(f"Hata: yt-dlp çalıştırılamadı.\n{e.stderr}")
        return None
    except Exception as e:
        print(f"Hata: {e}")
        return None

class StreamingHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            stream_url = get_youtube_stream_url(YOUTUBE_URL)
            if not stream_url:
                print("Could not get stream URL.")
                return

            print(f"[*] OpenCV ile bağlantı kuruluyor: {stream_url[:50]}...")
            cap = cv2.VideoCapture(stream_url)

            if not cap.isOpened():
                print("Error: Could not open video stream.")
                return

            print("[*] Yayına başlandı. Hedef: 24 FPS")
            # 24 FPS target interval
            frame_interval = 1.0 / 24.0
            
            try:
                while True:
                    start_time = time.time()
                    
                    ret, img = cap.read()
                    if not ret:
                        print("Yayın sonlandı veya okunamadı.")
                        break

                    if model:
                        results = model(img, verbose=False)
                        annotated_img = results[0].plot()
                    else:
                        annotated_img = img

                    cv2.putText(annotated_img, "SunspotSDO 24 FPS STREAM - MARSPACE", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    
                    ret, jpeg = cv2.imencode('.jpg', annotated_img)
                    if not ret:
                        continue

                    frame = jpeg.tobytes()
                    self.wfile.write(b'--frame\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', str(len(frame)))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')

                    # 24 FPS Hız Limitleyici
                    elapsed = time.time() - start_time
                    sleep_time = frame_interval - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)

            except BrokenPipeError:
                pass
            except Exception as e:
                print(f"Streaming error: {e}")
            finally:
                cap.release()
        else:
            self.send_response(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == '__main__':
    server = StreamingServer(('', PORT), StreamingHandler)
    print(f"[*] YouTube YOLO Video Stream started at http://localhost:{PORT}/stream")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
