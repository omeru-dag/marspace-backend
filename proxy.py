import http.server
import socketserver
import urllib.request
import json
import os
import asyncio
import edge_tts
import uuid
import time
import re

PORT = 5500
LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"
WHISPER_SERVER_URL = "http://127.0.0.1:8080/inference"

# Global Status Variables
pending_triggers = []
current_solar_wind = 400 
current_gic = 0.5 
current_kp = 2.0
current_bz = 5.0
current_xray = "A1.0"
current_gic_amp = 0
current_trafo_temp = 45.0
current_freq = 50.00
current_sst = "AKTİF"
current_gps = "STABİL (LOCK)"
current_hf_noise = -110
current_nodes = 142

current_isolation_mode = "AKTİF (Bölgesel Ada Modu)"
current_marmaray = "STABİL"
current_yht = "AKTİF"
current_signaling = "STABİL"
current_gateway = "TA2THD-HUB"
current_band = "5.8 GHz / Yedek VHF"
current_packet_loss = "0.01%"

# Audio storage
AUDIO_DIR = "audio"
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

async def generate_tts(text, filename):
    communicate = edge_tts.Communicate(text, "tr-TR-AhmetNeural")
    await communicate.save(os.path.join(AUDIO_DIR, filename))

def whisper_inference(audio_path):
    """Local whisper.cpp serverına (Port 8080) WAV dosyasını gönderir."""
    boundary = uuid.uuid4().hex
    with open(audio_path, 'rb') as f:
        audio_content = f.read()
    
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"audio.wav\"\r\n"
        f"Content-Type: audio/wav\r\n\r\n"
    ).encode() + audio_content + f"\r\n--{boundary}--\r\n".encode()
    
    req = urllib.request.Request(
        WHISPER_SERVER_URL,
        data=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data.get("text", "").strip()
    except Exception as e:
        print(f"[!] Whisper Server Error: {e}")
        return ""

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
        global pending_triggers, current_solar_wind, current_gic, current_kp, current_bz
        global current_xray, current_gic_amp, current_trafo_temp, current_freq, current_sst
        global current_gps, current_hf_noise, current_nodes
        global current_isolation_mode, current_marmaray, current_yht, current_signaling
        global current_gateway, current_band, current_packet_loss

        if self.path.startswith('/audio/'):
            return super().do_GET()

        # TTS Endpoint
        if self.path.startswith('/tts'):
            try:
                parts = self.path.split('=')
                text = urllib.parse.unquote(parts[1]) if len(parts) > 1 else ""
                audio_filename = f"sys_{uuid.uuid4().hex[:8]}.mp3"
                asyncio.run(generate_tts(text, audio_filename))
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"audio_url": f"/audio/{audio_filename}"}).encode())
                return
            except Exception as e:
                print(f"[!] TTS Error: {e}")
                self.send_response(400); self.end_headers()
                return

        # Handle phase and telemetry setters
        if self.path.startswith('/set_'):
            try:
                parts = self.path.split('?')
                cmd = parts[0].replace('/set_', '')
                val = urllib.parse.unquote(parts[1].split('=')[1]) if (len(parts) > 1 and '=' in parts[1]) else None
                
                if val is not None:
                    if cmd == 'phase': pending_triggers.append(int(val))
                    elif cmd == 'wind': globals()['current_solar_wind'] = int(float(val))
                    elif cmd == 'kp': globals()['current_kp'] = float(val)
                    elif cmd == 'bz': globals()['current_bz'] = float(val)
                    elif cmd == 'gic_amp': globals()['current_gic_amp'] = int(float(val))
                    elif cmd == 'freq': globals()['current_freq'] = float(val)
                    elif cmd == 'marmaray': globals()['current_marmaray'] = val
                    elif cmd == 'yht': globals()['current_yht'] = val
                    elif cmd == 'signaling': globals()['current_signaling'] = val
                    elif cmd == 'nodes': globals()['current_nodes'] = int(val)
                
                self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
            except Exception as e:
                print(f"[!] Set Error: {e}")
                self.send_response(400); self.end_headers()
            return

        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            trigger = pending_triggers.pop(0) if pending_triggers else None
            status_data = {
                "trigger_phase": trigger,
                "solar_wind": current_solar_wind, "gic": current_gic, "kp": current_kp, "bz": current_bz,
                "xray": current_xray, "gic_amp": current_gic_amp, "trafo_temp": current_trafo_temp,
                "freq": current_freq, "sst": current_sst, "gps": current_gps, "hf_noise": current_hf_noise,
                "nodes": current_nodes, "isolation_mode": current_isolation_mode, "marmaray": current_marmaray,
                "yht": current_yht, "signaling": current_signaling, "gateway": current_gateway,
                "band": current_band, "packet_loss": current_packet_loss
            }
            self.wfile.write(json.dumps(status_data).encode('utf-8'))
            return

        super().do_GET()

    def do_POST(self):
        if self.path == '/voice_command':
            content_length = int(self.headers['Content-Length'])
            audio_data = self.rfile.read(content_length)
            
            print(f"[*] /voice_command: Received {content_length} bytes of audio")
            
            # Save to temporary WAV
            with open("temp_voice.wav", "wb") as f:
                f.write(audio_data)
            
            # Send to Whisper
            print(f"[*] Forwarding to Whisper: {WHISPER_SERVER_URL}")
            user_text = whisper_inference("temp_voice.wav")
            
            if user_text:
                print(f"[*] Whisper Transcribed: '{user_text}'")
            else:
                print(f"[!] Whisper failed or returned empty text.")
                user_text = "[ANLAŞILAMADI VEYA SESSİZ DİNLEME]"

            # Send to LM Studio
            ai_text = "Askeri sunucu bağlantı hatası."
            try:
                print(f"[*] Forwarding to LM Studio: {user_text}")
                llm_payload = {
                    "model": "local-model",
                    "messages": [
                        {"role": "system", "content": "Sen MARSPACE otonom yapay zekasisin. KONTROL MERKEZİ'nden gelen sesli komutu işle.\nEğer kullanıcı bir fazı (Faz 1, Faz 2, Faz 3, Faz 4) aktifleştirmek istiyorsa, cevabının sonuna MUTLAKA [ACTION: PHASE#] etiketini ekle. Örn: [ACTION: PHASE1].\nKısa ve operasyonel yanıt ver."},
                        {"role": "user", "content": user_text}
                    ],
                    "temperature": 0.7
                }
                
                req = urllib.request.Request(LM_STUDIO_URL, data=json.dumps(llm_payload).encode(), headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    resp_json = json.loads(resp.read().decode())
                    ai_text = resp_json['choices'][0]['message']['content']
                    print(f"[*] AI Response: '{ai_text}'")
            except Exception as e:
                print(f"[!] AI Forward Error: {e}")

            # TTS (Aksiyon etiketlerini sesten temizle)
            tts_text = re.sub(r'\[ACTION: PHASE\d+\]', '', ai_text).strip()
            unique_id = uuid.uuid4().hex
            audio_filename = f"resp_{unique_id}.mp3"
            asyncio.run(generate_tts(tts_text, audio_filename))
            
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"user_text": user_text, "ai_text": ai_text, "audio_url": f"/audio/{audio_filename}"}).encode())
            return

        elif self.path == '/api/v1/chat':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                print(f"[*] /api/v1/chat: Forwarding to LM Studio: {post_data.decode()[:50]}...")
                req = urllib.request.Request(LM_STUDIO_URL, data=post_data, headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req) as resp:
                    resp_data = resp.read()
                    print(f"[*] /api/v1/chat: Received from LM Studio: {resp_data.decode()[:50]}...")
                    self.send_response(resp.status)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(resp_data)
            except Exception as e:
                print(f"[!] /api/v1/chat Error: {e}")
                self.send_response(500); self.end_headers()
        else:
            self.send_response(404); self.end_headers()

import urllib.parse
from http.server import ThreadingHTTPServer

def run(server_class=ThreadingHTTPServer, handler_class=ProxyHTTPRequestHandler):
    server_address = ('', PORT)
    httpd = server_class(server_address, handler_class)
    print(f"MARSPACE Military Proxy (Threading mode) active on port {PORT}")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
