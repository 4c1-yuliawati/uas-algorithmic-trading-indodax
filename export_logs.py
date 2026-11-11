"""Tarik log mentah dari bot (Redis via /api/export) -> data/*.csv untuk hitung_ulang.py.
Pakai: BOT_URL=https://<app>.vercel.app CRON_SECRET=... python export_logs.py"""
import os, csv, json, urllib.request, datetime as dt, pathlib
D = pathlib.Path(__file__).parent / "data"; D.mkdir(exist_ok=True)
rq = urllib.request.Request(os.environ["BOT_URL"] + "/api/export", headers={"Authorization": "Bearer " + os.environ["CRON_SECRET"]})
L = json.load(urllib.request.urlopen(rq, timeout=60))
json.dump(L, open(D / "log_mentah.json", "w"))            # arsip mentah utuh (ikut dikumpulkan)
def w(name, cols, rows):
    with open(D / name, "w", newline="") as f:
        c = csv.writer(f); c.writerow(cols); [c.writerow([r.get(k) for k in cols]) for r in rows]
w("calls.csv", ["candle_ts", "processed_ts", "ts", "status"], L["calls"])
w("orders.csv", ["ts", "pair", "side", "qty", "best_bid", "best_ask", "fill", "fee", "signal_price", "candle_ts"], L["orders"])
w("equity_forward.csv", ["date", "equity"], L["equity"])
w("errors.csv", ["ts", "type", "msg"], L["errors"]); w("killswitch.csv", ["ts", "action"], L["kill"])
w("snapshots.csv", ["ts", "pair", "bid", "ask"], L["snaps"])
w("signals_forward.csv", ["candle_ts", "pair", "signal"], [s for s in L["signals"]])
print({k: len(v) for k, v in L.items() if isinstance(v, list)})

# btc_close.csv: tambah close BTC/IDR dari log sinyal (untuk buy&hold forward); format tanggal sama dgn backtest.py
bc = {}
if (D / "btc_close.csv").exists():
    bc = {r["date"]: r["close"] for r in csv.DictReader(open(D / "btc_close.csv"))}
for s in L["signals"]:
    if s["pair"] == "btcidr" and s.get("c"): bc[dt.datetime.fromtimestamp(s["candle_ts"] + 43200, dt.timezone.utc).strftime("%Y-%m-%d")] = s["c"]
with open(D / "btc_close.csv", "w", newline="") as f:
    c = csv.writer(f); c.writerow(["date", "close"]); [c.writerow([k, bc[k]]) for k in sorted(bc)]
# ringkasan kesehatan bot (cek cepat)
from collections import Counter
cl = L["calls"]; print("panggilan:", len(cl), "| status:", dict(Counter(x["status"] for x in cl)))
print("error per jenis:", dict(Counter(x["type"] for x in L["errors"])))
if cl: print("panggilan terakhir:", dt.datetime.fromtimestamp(cl[-1]["ts"], dt.timezone(dt.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M WIB"))
