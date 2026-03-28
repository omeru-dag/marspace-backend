import http.server
import socketserver
import cv2
import os
import time
from ultralytics import YOLO

PORT = 5001
IMAGE_DIR = r"C:\Users\dagom\OneDrive\Belgeler\codes\TUA ARAYÜZ Programı\SunspotsYoloDataset_V2\SunspotsYoloDataset\test\images"
MODEL_PATH = "SunspotSDO_yolo.pt"

print(f"[*] YOLO model yükleniyor: {MODEL_PATH}")
try:
    model = YOLO(MODEL_PATH)
    print(f"[*] Model yüklendi. Görüntüler dizini: {IMAGE_DIR}")
except Exception as e:
    print(f"Hata: YOLO modeli yüklenemedi: {e}")
    model = None

class StreamingHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            if not os.path.exists(IMAGE_DIR):
                print(f"Hata: {IMAGE_DIR} dizini bulunamadı!")
                return

            images = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            images.sort()

            if not images:
                print("No images found in the directory.")
                return

            try:
                while True:
                    for img_name in images:
                        img_path = os.path.join(IMAGE_DIR, img_name)
                        img = cv2.imread(img_path)
                        
                        if img is None:
                            continue

                        if model:
                            # Run YOLO inference
                            results = model(img, verbose=False)
                            # Get annotated image
                            annotated_img = results[0].plot()
                        else:
                            annotated_img = img

                        # Add text
                        cv2.putText(annotated_img, "SDO REAL-TIME ANALYSIS - MARSPACE", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
                        # Encode image as JPEG
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
                        
                        time.sleep(0.5)
            except BrokenPipeError:
                pass
            except Exception as e:
                print(f"Streaming error: {e}")
        else:
            self.send_response(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == '__main__':
    server = StreamingServer(('', PORT), StreamingHandler)
    print(f"[*] Sunspot Video Stream started at http://localhost:{PORT}/stream")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
