"""Diagnosis konektivitas Vercel -> Indodax (PUBLIK, baca-saja, tanpa secret). Dipakai untuk uji koneksi sebelum freeze."""
import os, sys, json, time, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler
_n = int(time.time())
URLS = ["https://indodax.com/api/server_time", "https://indodax.com/api/depth/btcidr", f"https://indodax.com/tradingview/history_v2?symbol=BTCIDR&tf=240&from={_n - 86400 * 30}&to={_n}", "https://indodax.com/api/pairs"]
UAS = {"bot": "Mozilla/5.0 (compatible; uas-dryrun-bot/1.0)", "browser": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36", "python_default": None}
def probe(url, ua):
    h = {"Accept": "application/json, text/plain, */*"}
    if ua: h["User-Agent"] = ua
    t = time.time()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=10) as r:
            b = r.read(200).decode("utf-8", "replace"); return dict(code=r.status, ms=int((time.time() - t) * 1000), body=b[:120], server=r.headers.get("server"))
    except urllib.error.HTTPError as e:
        return dict(code=e.code, ms=int((time.time() - t) * 1000), body=e.read(200).decode("utf-8", "replace")[:120], server=e.headers.get("server"), cf_ray=e.headers.get("cf-ray"))
    except Exception as e: return dict(error=str(e)[:150])
def pipeline(pair="btcidr"):
    try:
        import _core
        now = _core.server_time(); TF = 43200; cand = now // TF * TF - TF
        c4 = _core.candles_4h(pair, now); b12 = _core.bars_12h(c4, TF)
        ts = sorted(c4)
        return dict(now=now, cand=cand, n4=len(c4), first4=ts[:1], last4=ts[-6:], last4_mod=[t % 14400 for t in ts[-3:]],
                    n12=len(b12), last12=[(t, ok) for t, _, ok in b12[-4:]], last12_is_cand=bool(b12) and b12[-1][0] == cand)
    except Exception as e: return dict(error=repr(e)[:300])
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        out = dict(region=os.environ.get("VERCEL_REGION"), pipeline=pipeline(), results={f"{(u.split('/api/')[1] if '/api/' in u else 'history_v2')[:20]}|{k}": probe(u, v) for u in URLS for k, v in UAS.items()})
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(json.dumps(out, indent=1).encode())
