"""Backtest 12 jam, data Indodax asli. Pakai: python backtest.py [--data DIR] [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--window]
--window = jalankan ulang di jendela forward (config fwd_start/fwd_end) -> file *_window* untuk dashboard.
Eksekusi: sinyal di close bar t -> fill di OPEN bar t+1 +- (spread/2 + slippage) + fee taker (sama dgn AFL: delay 1 bar, harga open)."""
import csv, json, sys, argparse, pathlib, datetime as dt
from strategy import raw_signals, decide
R = pathlib.Path(__file__).parent; cfg = json.load(open(R / "config.json"))
ap = argparse.ArgumentParser(); ap.add_argument("--data", default=str(R / "data_hist/indodax_12h"))
ap.add_argument("--start"); ap.add_argument("--end"); ap.add_argument("--window", action="store_true")
ap.add_argument("--cost-mult", type=float, default=1.0); ap.add_argument("--out", default=str(R / "data"))
a = ap.parse_args()
TF = cfg["tf_sec"]; UTC = dt.timezone.utc; WIB = dt.timezone(dt.timedelta(hours=7))
if a.window:
    s0 = dt.datetime.fromisoformat(cfg["fwd_start"]).astimezone(UTC); s1 = dt.datetime.fromisoformat(cfg["fwd_end"]).astimezone(UTC)
else:
    s0 = dt.datetime.fromisoformat(a.start or cfg["backtest_start"]).replace(tzinfo=UTC); s1 = dt.datetime.fromisoformat(a.end or cfg["backtest_end"]).replace(tzinfo=UTC)
t0, t1 = int(s0.timestamp()), int(s1.timestamp())
fb, fs = cfg["fee_buy_pct"] / 100 * a.cost_mult, cfg["fee_sell_pct"] / 100 * a.cost_mult
hs = cfg["backtest_spread_pct"] / 200 * a.cost_mult; sl = cfg["backtest_slip_pct"] / 100 * a.cost_mult

def load(pair):
    rows = []
    for r in csv.DictReader(open(f"{a.data}/{pair[:-3].upper()}.csv")):
        d = dt.datetime.strptime(r["t"], "%Y-%m-%d %H").replace(tzinfo=UTC) if " " in r["t"] else dt.datetime.strptime(r["t"], "%Y-%m-%d").replace(tzinfo=UTC)
        rows.append(dict(ts=int(d.timestamp()), o=float(r["o"]), h=float(r["h"]), l=float(r["l"]), c=float(r["c"]), v=float(r["v"])))
    return rows
B = {p: load(p) for p in cfg["universe"]}
SIG = {}; IDX = {}
for p, bars in B.items():
    bs, ss = raw_signals(bars); SIG[p] = (bs, ss); IDX[p] = {b["ts"]: i for i, b in enumerate(bars)}
grid = sorted({b["ts"] for bars in B.values() for b in bars if t0 < b["ts"] + TF <= t1})   # candle yang TUTUP di (t0, t1]
cash = cfg["capital"]; pos = {}; trades = []; eq_rows = []; sigs = []; day0 = {}; blocked = None
def mark(ts):
    tot = cash
    for p, q in pos.items():
        i = IDX[p].get(ts)
        if i is not None: q["last"] = B[p][i]["c"]
        tot += q["qty"] * q["last"] * (1 - hs)       # nilai pada ~bid
    return tot
for ts in grid:
    day = dt.datetime.fromtimestamp(ts + TF, WIB).date()   # hari WIB saat keputusan dibuat (close bar)
    eq = mark(ts); day0.setdefault(day, eq)
    blocked = (eq / day0[day] - 1) * 100 <= -cfg["daily_loss_limit_pct"]
    nxt = ts + TF; todo = []
    for p in cfg["universe"]:
        i = IDX[p].get(ts)
        if i is None or i < 1: continue
        act = decide(SIG[p][0][i], SIG[p][1][i], p in pos)
        sigs.append((ts, p, act)); todo.append((p, act, B[p][i]["c"]))
    for p, act, sp in [x for x in todo if x[1] == "SELL"] + [x for x in todo if x[1] == "BUY"]:
        j = IDX[p].get(nxt)
        if j is None: continue
        o = B[p][j]["o"]
        if act == "SELL":
            q = pos.pop(p); fill = o * (1 - hs - sl); gross = q["qty"] * fill; fee = gross * fs; cash += gross - fee
            trades.append(dict(pair=p, entry_ts=q["ts"], exit_ts=nxt, qty=q["qty"], entry_fill=q["fill"], exit_fill=fill,
                fee=q["fee"] + fee, spread_cost=q["qty"] * (q["o"] + o) * hs, slip_cost=q["qty"] * (q["o"] + o) * sl))
        elif act == "BUY" and not blocked and len(pos) < cfg["max_positions"]:
            size = min(cfg["alloc_pct"] / 100 * eq, cash) / (1 + fb)
            if size < cfg["min_order"]: continue
            fill = o * (1 + hs + sl); qty = int(size / fill * 1e8) / 1e8; cost = qty * fill; fee = cost * fb
            if qty <= 0 or cost < cfg["min_order"]: continue
            cash -= cost + fee; pos[p] = dict(qty=qty, fill=fill, fee=fee, ts=nxt, o=o, last=o)
    eq_rows.append((dt.datetime.fromtimestamp(ts + TF, UTC).strftime("%Y-%m-%d"), mark(ts)))
daily = {}
for d, e in eq_rows: daily[d] = e            # equity penutup hari (UTC)
out = pathlib.Path(a.out); out.mkdir(exist_ok=True); sfx = "_window" if a.window else ""
with open(out / f"backtest{sfx}_equity.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["date", "equity"]); [w.writerow([d, round(e, 2)]) for d, e in daily.items()]
with open(out / f"backtest{sfx}_trades.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(trades[0].keys()) if trades else ["pair","entry_ts","exit_ts","qty","entry_fill","exit_fill","fee","spread_cost","slip_cost"]); w.writeheader(); w.writerows(trades)
with open(out / ("signals_backtest_window.csv" if a.window else "backtest_signals.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["candle_ts", "pair", "signal"]); [w.writerow([t, p, s]) for t, p, s in sigs]
if not a.window:
    with open(out / "btc_close.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["date", "close"]); bd = {}
        for b in B.get("btcidr", []):
            if t0 < b["ts"] + TF <= t1: bd[dt.datetime.fromtimestamp(b["ts"] + TF, UTC).strftime("%Y-%m-%d")] = b["c"]
        [w.writerow([d, c]) for d, c in bd.items()]
e = list(daily.values()); peak = e[0]; mdd = 0
for x in e: peak = max(peak, x); mdd = min(mdd, x / peak - 1)
yrs = (s1 - s0).days / 365.25; pn = [t["qty"] * (t["exit_fill"] - t["entry_fill"]) - t["fee"] for t in trades]
print(f"{'WINDOW' if a.window else 'BACKTEST'} {s0.date()}->{s1.date()} costx{a.cost_mult}: ret {e[-1]/cfg['capital']-1:+.2%} CAGR {(e[-1]/cfg['capital'])**(1/yrs)-1:+.2%} MDD {mdd:.2%} trades {len(trades)} win {sum(x>0 for x in pn)/max(1,len(pn)):.1%} open_pos {len(pos)}")
