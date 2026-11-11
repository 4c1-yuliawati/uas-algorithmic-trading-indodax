import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
"""Publik, baca-saja: ringkasan log untuk halaman dashboard Vercel (tanpa secret, tanpa snapshot mentah)."""
import json
from http.server import BaseHTTPRequestHandler
from _core import *
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        g = lambda k, a=0, b=-1: [json.loads(x) for x in redis("LRANGE", "log:" + k, a, b) or []]
        st = json.loads(redis("GET", "state") or "null") or {}
        d = dict(cfg={k: CFG[k] for k in ["strategy_name", "universe", "tf_sec", "capital", "fwd_start", "fwd_end", "fee_buy_pct", "fee_sell_pct", "max_positions", "alloc_pct", "daily_loss_limit_pct"]},
                 state=dict(cash=st.get("cash"), pos=st.get("pos", {}), last=st.get("last", {}), day=st.get("day")),
                 calls=g("calls"), orders=g("orders"), equity=g("equity"), errors=g("errors", -300, -1), kill=g("kill"),
                 snaps_n=redis("LLEN", "log:snaps"), kill_flag=redis("GET", "kill") == "1" or os.environ.get("KILL_SWITCH") == "1")
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Cache-Control", "no-store"); self.end_headers()
        self.wfile.write(json.dumps(d).encode())
