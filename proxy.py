import http.server
import socketserver
import urllib.request
import json

PORT = 5500
LM_STUDIO_URL = "http://127.0.0.1:1234/api/v1/chat"

# Dışarıdan (örneğin telefondan veya başka yazılımdan) gelecek tetiklemeleri kuyrukta tutar
pending_triggers = []
current_solar_wind = 400 
current_gic = 0.5 
current_kp = 2.0
current_bz = 5.0

class ProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.end_headers()

    def do_GET(self):
        global pending_triggers
        if self.path.startswith('/set_phase'):
            try:
                phase = int(self.path.split('=')[1])
                pending_triggers.append(phase)
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(f"HARIKA! Ana arayuz otomatik olarak Faz {phase} durumuna gececek.".encode('utf-8'))
            except Exception:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Hatali parametre. Ornek kullanim: /set_phase?phase=2")
        elif self.path.startswith('/set_wind'):
            try:
                global current_solar_wind
                val = int(self.path.split('=')[1])
                current_solar_wind = val
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(f"Ruzgar hizi guncellendi: {val} km/s".encode('utf-8'))
            except Exception:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Hatali parametre. Ornek kullanim: /set_wind?val=850")
        elif self.path.startswith('/set_gic'):
            try:
                global current_gic
                val = float(self.path.split('=')[1])
                current_gic = val
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(f"GIC akimi guncellendi: {val} A/km".encode('utf-8'))
            except Exception:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Hatali parametre. Ornek kullanim: /set_gic?val=12.5")
        elif self.path.startswith('/set_kp'):
            try:
                global current_kp
                val = float(self.path.split('=')[1])
                current_kp = val
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(f"Kp indeksi guncellendi: {val}".encode('utf-8'))
            except Exception:
                self.send_response(400)
                self.end_headers()
        elif self.path.startswith('/set_bz'):
            try:
                global current_bz
                val = float(self.path.split('=')[1])
                current_bz = val
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(f"Bz alani guncellendi: {val} nT".encode('utf-8'))
            except Exception:
                self.send_response(400)
                self.end_headers()
        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            phase_to_trigger = pending_triggers.pop(0) if pending_triggers else None
            self.wfile.write(json.dumps({
                "trigger_phase": phase_to_trigger,
                "solar_wind": current_solar_wind,
                "gic": current_gic,
                "kp": current_kp,
                "bz": current_bz
            }).encode('utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/v1/chat':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                req = urllib.request.Request(LM_STUDIO_URL, data=post_data, headers={'Content-Type': 'application/json'})
                with open("proxy_debug.log", "a") as f:
                    f.write(f"\n[POST] Forwarding to {LM_STUDIO_URL}\nData: {post_data.decode('utf-8', errors='ignore')}\n")
                
                with urllib.request.urlopen(req) as response:
                    res_body = response.read()
                    self.send_response(response.status)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(res_body)
            except Exception as e:
                with open("proxy_debug.log", "a") as f:
                    f.write(f"[ERROR] {str(e)}\n")
                print(f"LM Studio Forwarding Error: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), ProxyHTTPRequestHandler) as httpd:
    print(f"Proxy Server çalışıyor! CORS destekli (Her Yerden Çalışır). Port: {PORT}")
    httpd.serve_forever()
