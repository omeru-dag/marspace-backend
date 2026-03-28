import cv2
import http.server
import socketserver
import time
import os

PORT = 5006
VIDEO_PATH = "youtube_sunspot_processed.mp4"

class StreamingHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        if self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            if not os.path.exists(VIDEO_PATH):
                print(f"Hata: {VIDEO_PATH} bulunamadi.")
                return

            print(f"[*] Yayina basliyor (PROCESSED FEED): {VIDEO_PATH}")
            cap = cv2.VideoCapture(VIDEO_PATH)
            
            try:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = cap.read()
                        if not ret: break
                    
                    # Add technical overlay even on processed video
                    cv2.putText(frame, "MARSPACE OTONOM ANALIZ (LOCAL ENGINE)", (15, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    data = jpeg.tobytes()
                    
                    try:
                        self.wfile.write(b'--frame\r\n')
                        self.send_header('Content-Type', 'image/jpeg')
                        self.send_header('Content-Length', str(len(data)))
                        self.end_headers()
                        self.wfile.write(data)
                        self.wfile.write(b'\r\n')
                        self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError):
                        break
                    
                    # 24-30 FPS approx
                    time.sleep(0.033)
            except Exception as e:
                print(f"Stream hatasi: {e}")
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
    print(f"[*] Loop Streamer baslatildi: http://localhost:{PORT}/stream")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
