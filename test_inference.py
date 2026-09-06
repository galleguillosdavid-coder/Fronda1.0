import urllib.request
import json
import time

print("[Test] Sending inference request to http://127.0.0.1:11434/api/generate ...")
payload = {
    "model": "frondabrick",
    "prompt": "Hola Fronda Brick, confirma tu estado operativo.",
    "stream": False,
    "options": {
        "temperature": 0.3,
        "num_ctx": 2048
    }
}
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(
    "http://127.0.0.1:11434/api/generate",
    data=data,
    headers={"Content-Type": "application/json"}
)

t0 = time.time()
try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        res = json.loads(resp.read().decode())
        elapsed = time.time() - t0
        print(f"[OK] Response received in {elapsed:.2f}s:")
        print(res.get("response"))
except Exception as e:
    print(f"[FAIL] Error: {e}")
