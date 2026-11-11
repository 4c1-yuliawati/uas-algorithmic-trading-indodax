import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from _core import *
class handler(BaseHTTPRequestHandler):
    def do_GET(self):   # /api/kill?on=1 (nyalakan) | ?on=0 (matikan); wajib header Authorization: Bearer CRON_SECRET
        if not authorized(self.headers): self.send_response(401); self.end_headers(); return
        on = parse_qs(urlparse(self.path).query).get("on", ["1"])[0]
        redis("SET", "kill", "1" if on == "1" else "0"); log("kill", dict(ts=int(time.time()), action="KILL_ON" if on == "1" else "KILL_OFF"))
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
