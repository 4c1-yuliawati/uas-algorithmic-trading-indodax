"""Jalankan di LAPTOP (bukan Vercel) SETELAH 14 Nov 12.00 WIB: tarik bar 1 jam Indodax mundur, susun 12 jam,
gabung ke data_hist/indodax_12h/*.csv agar `python backtest.py --window` bisa dijalankan pada candle yang sama.
Maks ~3 request/detik, tidak paralel. Pakai: python update_hist.py"""
import csv, json, sys, time, pathlib, datetime as dt
R = pathlib.Path(__file__).parent; sys.path.insert(0, str(R / "api"))
from _core import _row, http_json, BASE
cfg = json.load(open(R / "config.json")); TF = cfg["tf_sec"]; UTC = dt.timezone.utc

def agg12(rows, now):
    """rows: {ts_1jam: bar}. Hanya bucket 12 jam LENGKAP (12 bar) & sudah tertutup."""
    g = {}
    for t in sorted(rows): g.setdefault(t - t % TF, []).append(rows[t])
    out = {}
    for k, s in g.items():
        if len(s) == TF // 3600 and k + TF <= now:
            out[k] = dict(o=s[0]["o"], h=max(x["h"] for x in s), l=min(x["l"] for x in s), c=s[-1]["c"], v=sum(x["v"] for x in s))
    return out

def pull(sym, t_from, t_to):
    got, to = {}, t_to
    for _ in range(40):
        d = http_json(f"{BASE}/tradingview/history_v2?symbol={sym.upper()}&tf=60&from={t_from}&to={to}")
        rows = [_row(x) for x in (d if isinstance(d, list) else d.get("data", []))]
        if not rows: break
        for t, b in rows: got[t] = b
        e = min(t for t, _ in rows)
        if e <= t_from or e >= to: break
        to = e; time.sleep(0.4)
    return {t: b for t, b in got.items() if t + 3600 <= t_to}

if __name__ == "__main__":
    now = int(time.time())
    for p in cfg["universe"]:
        f = R / "data_hist/indodax_12h" / f"{p[:-3].upper()}.csv"; old = {}
        for r in csv.DictReader(open(f)):
            old[int(dt.datetime.strptime(r["t"], "%Y-%m-%d %H").replace(tzinfo=UTC).timestamp())] = r
        start = max(old) - 3 * 86400
        new = agg12(pull(p, start, now), now); n0 = len(old)
        for k, b in new.items():
            if k not in old:   # data lama tidak ditimpa
                old[k] = dict(t=dt.datetime.fromtimestamp(k, UTC).strftime("%Y-%m-%d %H"), o=b["o"], h=b["h"], l=b["l"], c=b["c"], v=b["v"])
        with open(f, "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["t", "o", "h", "l", "c", "v"])
            for k in sorted(old): r = old[k]; w.writerow([dt.datetime.fromtimestamp(k, UTC).strftime("%Y-%m-%d %H"), r["o"], r["h"], r["l"], r["c"], r["v"]])
        print(p, "bar baru:", len(old) - n0, "terakhir:", dt.datetime.fromtimestamp(max(old), UTC)); time.sleep(0.4)
