import urllib.request
import json

url = "http://localhost:5500/api/v1/chat"
data = {
    "model": "google/gemma-3-1b",
    "system_prompt": "Test",
    "input": "Hello"
}

print(f"[*] Testing {url}...")
try:
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        print(f"[+] Status: {resp.status}")
        print(f"[+] Body: {resp.read().decode()}")
except Exception as e:
    print(f"[-] Error: {e}")
    if hasattr(e, 'read'):
        print(f"[-] Response Body: {e.read().decode()}")
