"""Uji OFFLINE bot (Redis & Indodax TIRUAN, data historis asli 12 jam dipecah jadi bar 4 jam).
Membuktikan: (1) sinyal bot == backtest candle demi candle, (2) idempotency (panggilan ganda tidak membeli lagi),
(3) walk order book + fee. Pakai: python tests/sim_bot.py [--out L.json]   (hanya untuk uji; bukan log forward)"""
import sys, os, json, csv, datetime as dt, pathlib, subprocess
R = pathlib.Path(__file__).resolve().parent.parent; sys.path[:0] = [str(R / "api"), str(R)]
os.environ.update(CRON_SECRET="x", UPSTASH_REDIS_REST_URL="u", UPSTASH_REDIS_REST_TOKEN="t")
import _core, tick
UTC = dt.timezone.utc; H = {}
for p in tick.U:
    rows = []
    for r in csv.DictReader(open(R / f"data_hist/indodax_12h/{p[:-3].upper()}.csv")):
        t = int(dt.datetime.strptime(r["t"], "%Y-%m-%d %H").replace(tzinfo=UTC).timestamp()); o, h, l, c, v = (float(r[k]) for k in "ohlcv")
        rows += [(t, dict(o=o, h=h, l=o, c=o, v=v / 3)), (t + 14400, dict(o=o, h=o, l=l, c=o, v=v / 3)), (t + 28800, dict(o=o, h=o, l=o, c=c, v=v / 3))]
    H[p] = rows
KV, NOW = {}, [0]
def fake_redis(*c):
    k = c[0]
    if k == "RPUSH": KV.setdefault(c[1], []).append(c[2]); return 1
    if k == "GET": return KV.get(c[1])
    if k == "SET":
        if "NX" in c and c[1] in KV: return None
        KV[c[1]] = c[2]; return "OK"
    if k == "DEL": KV.pop(c[1], None); return 1
_core.redis = tick.redis = fake_redis
tick.candles_4h = lambda p, now, need=0: {t: b for t, b in H[p] if t + 14400 <= now}
def fake_depth(p):
    px = next(b["c"] for t, b in reversed(H[p]) if t + 14400 <= NOW[0])
    return [(px * .999, 1e6), (px * .99, 1e6)], [(px * 1.001, 1e6), (px * 1.01, 1e6)]
tick.depth = fake_depth; tick.time.sleep = lambda s: None; tick.server_time = lambda: NOW[0]
a, b = int(dt.datetime(2024, 1, 1, tzinfo=UTC).timestamp()), int(dt.datetime(2024, 4, 1, tzinfo=UTC).timestamp())
for now in range(a, b, 3600):                         # cron tiap jam, menit ke-7
    NOW[0] = now + 420; tick.time.time = lambda n=NOW[0]: n; tick.run()
    if now == a + 36000: tick.run()                   # panggilan ganda
L = {k: [json.loads(x) for x in KV.get("log:" + k, [])] for k in ["calls", "orders", "equity", "errors", "snaps", "signals", "kill"]}
L["state"] = json.loads(KV["state"])
if "--out" in sys.argv: json.dump(L, open(sys.argv[sys.argv.index("--out") + 1], "w"))
# --- asersi ---
import strategy
import tempfile
tmp = tempfile.mkdtemp()
subprocess.run([sys.executable, str(R / "backtest.py"), "--start", "2024-01-01", "--end", "2024-04-01", "--out", tmp], check=True, capture_output=True)
ref = {(int(r["candle_ts"]), r["pair"]): r["signal"] for r in csv.DictReader(open(tmp + "/backtest_signals.csv"))}
n = bad = 0
for s in L["signals"]:
    if s["signal"] != "INVALID" and (s["candle_ts"], s["pair"]) in ref: n += 1; bad += ref[(s["candle_ts"], s["pair"])] != s["signal"]
dup = sum(c["status"] == "DUPLIKAT_DILEWATI" for c in L["calls"]); proc = sum(c["status"] == "PROCESSED" for c in L["calls"])
print(f"panggilan {len(L['calls'])}, diproses {proc}, duplikat dilewati {dup}; sinyal dibandingkan {n}, beda {bad}; order {len(L['orders'])}")
assert bad == 0, "sinyal bot != strategi langsung"; assert len({c["candle_ts"] for c in L["calls"] if c["status"] == "PROCESSED"}) == proc, "candle diproses >1x"
for o in L["orders"]: assert o["fill"] >= o["best_ask"] - 1e-6 if o["side"] == "BUY" else o["fill"] <= o["best_bid"] + 1e-6, "fill di luar bid/ask"
print("LOLOS")
