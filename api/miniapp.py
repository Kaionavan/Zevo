import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

KV_URL   = os.environ.get("KV_REST_API_URL", "")
KV_TOKEN = os.environ.get("KV_REST_API_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "7732138103"))

def kv_get(key):
    if not KV_URL: return None
    try:
        req = urllib.request.Request(
            f"{KV_URL}/get/{key}",
            headers={"Authorization": f"Bearer {KV_TOKEN}"}
        )
        res = json.loads(urllib.request.urlopen(req, timeout=3).read())
        val = res.get("result")
        return json.loads(val) if val else None
    except:
        return None

def kv_set(key, value):
    if not KV_URL: return
    try:
        req = urllib.request.Request(
            f"{KV_URL}/pipeline",
            data=json.dumps([["SET", key, json.dumps(value)]]).encode(),
            headers={"Authorization": f"Bearer {KV_TOKEN}", "Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=3)
    except Exception as e:
        print(f"KV set error: {e}")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        uid_str = params.get("uid", [None])[0]
        is_admin = params.get("admin", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        # Admin — return all clients list
        if is_admin and uid_str and int(uid_str) == ADMIN_ID:
            client_ids = kv_get("all_clients") or []
            clients = []
            for cid in client_ids:
                c = kv_get(f"user:{cid}")
                if c:
                    c["_uid"] = cid
                    clients.append(c)
            self.wfile.write(json.dumps({"clients": clients}).encode())
            return

        # Regular user
        if uid_str:
            data = kv_get(f"user:{uid_str}") or {}
        else:
            data = {}

        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        uid_str = str(body.get("uid", ""))
        updates = body.get("updates", {})

        if uid_str and updates:
            user = kv_get(f"user:{uid_str}") or {}
            # Only allow safe fields
            safe = ["info_menu","info_hours","info_location","info_contacts","info_promo","info_faq"]
            for k, v in updates.items():
                if k in safe:
                    user[k] = v
            kv_set(f"user:{uid_str}", user)
            self.wfile.write(json.dumps({"ok": True}).encode())
        else:
            self.wfile.write(json.dumps({"ok": False}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, *args):
        pass
