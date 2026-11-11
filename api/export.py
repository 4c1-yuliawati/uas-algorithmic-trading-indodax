import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json
from http.server import BaseHTTPRequestHandler
from _core import *
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not authorized(self.headers): self.send_response(401); self.end_headers(); return
        d = {k: [json.loads(x) for x in redis("LRANGE", "log:" + k, 0, -1) or []] for k in ["calls", "orders", "equity", "errors", "snaps", "signals", "kill"]}
        d["state"] = json.loads(redis("GET", "state") or "null")
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(json.dumps(d).encode())
