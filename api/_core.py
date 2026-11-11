"""Helper bot: HTTP+retry, Redis (Upstash REST), parsing Indodax, walk order book. Hanya stdlib."""
import os, sys, json, time, hmac, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
CFG = json.load(open(os.path.join(ROOT, "config.json")))
BASE = "https://indodax.com"; UA = {"User-Agent": "Mozilla/5.0 (compatible; uas-dryrun-bot/1.0; +https://github.com/4c1-yuliawati/uas-algorithmic-trading-indodax)", "Accept": "application/json, text/plain, */*", "Accept-Language": "id-ID,id;q=0.9,en;q=0.8"}
class ApiError(Exception): pass

def http_json(url, method="GET", body=None, headers=None, tries=3, timeout=10):
    last = None
    for k in range(tries):                                  # retry TERBATAS (3x)
        try:
            rq = urllib.request.Request(url, data=body, method=method, headers=headers or UA)
            with urllib.request.urlopen(rq, timeout=timeout) as r:
                d = json.loads(r.read().decode())
            if d in (None, [], {}): raise ApiError("respons kosong")
            return d
        except Exception as e:
            last = e; time.sleep(0.4 * (2 ** k))
    raise ApiError(f"{url.split('?')[0]}: {last}")

def redis(*cmd):
    u, t = os.environ["UPSTASH_REDIS_REST_URL"], os.environ["UPSTASH_REDIS_REST_TOKEN"]
    d = http_json(u, "POST", json.dumps(list(cmd)).encode(), {"Authorization": "Bearer " + t, "Content-Type": "application/json"}, tries=3)
    return d.get("result")
def log(kind, rec): redis("RPUSH", "log:" + kind, json.dumps(rec, separators=(",", ":")))
def authorized(headers):
    s = os.environ.get("CRON_SECRET", "")
    return bool(s) and hmac.compare_digest(headers.get("authorization", headers.get("Authorization", "")), "Bearer " + s)

def server_time():
    d = http_json(BASE + "/api/server_time"); return int(d["server_time"] if isinstance(d, dict) else d)
def depth(pair):
    d = http_json(f"{BASE}/api/depth/{pair}")
    bids = [(float(p), float(q)) for p, q in d.get("buy", [])]; asks = [(float(p), float(q)) for p, q in d.get("sell", [])]
    return sorted(bids, reverse=True), sorted(asks)
KEYS = {"o": ("Open", "open", "o"), "h": ("High", "high", "h"), "l": ("Low", "low", "l"), "c": ("Close", "close", "c"), "v": ("Volume", "volume", "v")}
def _row(x):
    """toleran terhadap format history_v2 (dict Time/Open/High/Low/Close/Volume). VERIFIKASI di uji koneksi."""
    g = lambda ks: float(next(x[k] for k in ks if k in x))
    t = int(g(("Time", "time", "t"))); t = t // 1000 if t > 10**12 else t
    return t, {k: g(v) for k, v in KEYS.items()}
def candles_4h(pair, now, need=2700):
    """tarik mundur (to digeser ke bar paling awal), 4 jam; buang bar yang belum tertutup"""
    got, to = {}, now
    for _ in range(8):
        d = http_json(f"{BASE}/tradingview/history_v2?symbol={pair.upper()}&tf=240&from={to - 86400 * 200}&to={to}")
        rows = [_row(x) for x in (d if isinstance(d, list) else d.get("data", []))]
        if not rows: break
        for t, b in rows: got[t] = b
        e = min(t for t, _ in rows)
        if len(got) >= need or e >= to: break
        to = e; time.sleep(0.35)
    return {t: b for t, b in got.items() if t + 14400 <= now}   # hanya bar tertutup
def bars_12h(c4, tf=43200):
    """gabung 4h -> 12h (00/12 UTC); return list (ts, bar, lengkap)"""
    g = {}
    for t in sorted(c4): g.setdefault(t - t % tf, []).append((t, c4[t]))
    out = []
    for k in sorted(g):
        s = g[k]; ok = len(s) == tf // 14400
        out.append((k, dict(o=s[0][1]["o"], h=max(x[1]["h"] for x in s), l=min(x[1]["l"] for x in s), c=s[-1][1]["c"], v=sum(x[1]["v"] for x in s)), ok))
    return out
def walk(levels, qty):
    """habiskan level berikutnya; return (harga_rata2, terisi)"""
    need, cost = qty, 0.0
    for p, q in levels:
        t = min(q, need); cost += t * p; need -= t
        if need <= 1e-12: break
    f = qty - max(need, 0); return (cost / f if f else None), f
