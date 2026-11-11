"""hitung_ulang.py - hitung ulang SEMUA angka dashboard dari log mentah di data/.
Pakai: python hitung_ulang.py  -> dashboard.html (offline) + angka.json
Tidak ada angka yang ditulis manual; kolom CSV: lihat README_DASHBOARD.md"""
import json, math, pathlib
import pandas as pd
R = pathlib.Path(__file__).parent; D = R / "data"
cfg = json.load(open(R / "config.json", encoding="utf-8"))
if (R / "FREEZE.txt").exists(): cfg["freeze_commit"] = (R / "FREEZE.txt").read_text().split()[0]
TF = cfg["tf_sec"]
def rd(n):
    p = D / n
    return pd.read_csv(p) if p.exists() and p.stat().st_size > 5 else pd.DataFrame()

def cl(o):
    if isinstance(o, dict): return {k: cl(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [cl(v) for v in o]
    if hasattr(o, "item"): o = o.item()
    return None if isinstance(o, float) and (math.isnan(o) or math.isinf(o)) else o

def eq_m(df, cagr=False):
    if df.empty or len(df) < 2: return {}
    e = df.equity.astype(float); d = (pd.to_datetime(df.date.iloc[-1]) - pd.to_datetime(df.date.iloc[0])).days
    r = e.iloc[-1] / e.iloc[0] - 1
    m = {"ret": r, "mdd": (e / e.cummax() - 1).min(), "start": e.iloc[0], "end": e.iloc[-1], "days": d}
    if cagr and d >= 30: m["cagr"] = (1 + r) ** (365 / d) - 1
    return m

def tr_m(t):
    if t.empty: return {"n": 0}
    pnl = t.qty * (t.exit_fill - t.entry_fill) - t.fee
    cost = t.fee + t.spread_cost + t.slip_cost
    w, l = pnl[pnl > 0], pnl[pnl < 0]; gross = (pnl + cost).sum()
    return {"n": len(t), "win_rate": len(w) / len(t), "avg_win": w.mean() if len(w) else None,
            "avg_loss": l.mean() if len(l) else None, "pf": w.sum() / -l.sum() if len(l) else None,
            "net": pnl.sum(), "fee": t.fee.sum(), "spread": t.spread_cost.sum(), "slip": t.slip_cost.sum(),
            "gross": gross, "cost_share": cost.sum() / gross if gross > 0 else None}

def pair_orders(o):
    """order simulasi -> trade tertutup (rata-rata biaya, keluar proporsional)"""
    rows, op = [], {}
    for _, x in o.sort_values("ts").iterrows():
        sp = x.qty * (x.best_ask - x.best_bid) / 2
        sl = x.qty * ((x.fill - x.best_ask) if x.side == "BUY" else (x.best_bid - x.fill))
        if x.side == "BUY":
            p = op.setdefault(x.pair, dict(q=0, c=0, f=0, s=0, l=0, t=x.ts))
            p["q"] += x.qty; p["c"] += x.qty * x.fill; p["f"] += x.fee; p["s"] += sp; p["l"] += sl
        elif x.pair in op and op[x.pair]["q"] > 0:
            p = op[x.pair]; q = min(x.qty, p["q"]); fr = q / p["q"]
            rows.append(dict(pair=x.pair, entry_ts=p["t"], exit_ts=x.ts, qty=q, entry_fill=p["c"] / p["q"], exit_fill=x.fill,
                fee=p["f"] * fr + x.fee * q / x.qty, spread_cost=p["s"] * fr + sp * q / x.qty, slip_cost=p["l"] * fr + sl * q / x.qty))
            for k in "qcfsl": p[k] *= 1 - fr
    return pd.DataFrame(rows)

bt_eq, btw_eq, fw_eq, btc = rd("backtest_equity.csv"), rd("backtest_window_equity.csv"), rd("equity_forward.csv"), rd("btc_close.csv")
bt_tr, orders = rd("backtest_trades.csv"), rd("orders.csv")
W0 = int(pd.Timestamp(cfg["fwd_start"]).timestamp()); W1 = int(pd.Timestamp(cfg["fwd_end"]).timestamp())
def inwin(df, col="candle_ts"):   # candle yang TUTUP di (fwd_start, fwd_end]
    return df[(df[col] + TF > W0) & (df[col] + TF <= W1)] if not df.empty and col in df else df
orders = inwin(orders)
if not fw_eq.empty: fw_eq = fw_eq[(fw_eq.date >= cfg["fwd_start"][:10]) & (fw_eq.date <= cfg["fwd_end"][:10])]
btw_tr = rd("backtest_window_trades.csv")
fw_tr = pair_orders(orders) if not orders.empty else pd.DataFrame()

def bh(a, b):
    if btc.empty: return {}
    x = btc[(btc.date >= a) & (btc.date <= b)]
    return {"ret": x.close.iloc[-1] / x.close.iloc[0] - 1} if len(x) > 1 else {}
bt_a, bt_b = (bt_eq.date.iloc[0], bt_eq.date.iloc[-1]) if not bt_eq.empty else ("", "")
fa, fb = cfg["fwd_start"][:10], cfg["fwd_end"][:10]

# selisih fill forward vs backtest (jendela sama): pair + candle masuk sama
fills = []
if not fw_tr.empty and not btw_tr.empty:
    for _, f in fw_tr.iterrows():
        m = btw_tr[(btw_tr.pair == f.pair) & ((btw_tr.entry_ts - f.entry_ts).abs() < TF)]
        if len(m):
            b = m.iloc[0]; same_exit = abs(b.exit_ts - f.exit_ts) < TF
            fills.append(dict(pair=f.pair, entry_ts=f.entry_ts, entry_diff_pct=(f.entry_fill / b.entry_fill - 1) * 100,
                exit_diff_pct=(f.exit_fill / b.exit_fill - 1) * 100 if same_exit else None, delay_min=(f.entry_ts - b.entry_ts) / 60))
# kecocokan sinyal
sf, sb = inwin(rd("signals_forward.csv")), rd("signals_backtest_window.csv")
sig = {}
if not sf.empty and not sb.empty:
    m = sb.merge(sf, on=["candle_ts", "pair"], how="outer", suffixes=("_bt", "_fw"), indicator=True)
    m["ok"] = (m._merge == "both") & (m.signal_bt == m.signal_fw)
    sig = {"n": len(m), "match": m.ok.mean(), "beda": m[~m.ok][["candle_ts", "pair", "signal_bt", "signal_fw"]].fillna("").to_dict("records")[:200]}

# uptime
cl_ = inwin(rd("calls.csv")); up = {}
exp = int((pd.Timestamp(cfg["fwd_end"]) - pd.Timestamp(cfg["fwd_start"])).total_seconds() // TF)
if not cl_.empty:
    c = cl_.dropna(subset=["processed_ts"]).sort_values("processed_ts").drop_duplicates("candle_ts")
    c = c[c.processed_ts < c.candle_ts + 2 * TF]
    late = (c.processed_ts - (c.candle_ts + TF)) / 60
    up = {"expected": exp, "ontime": len(c), "uptime": len(c) / exp if exp else None, "calls": len(cl_),
          "late_med_min": late.median(), "late_max_min": late.max()}
er, ks = rd("errors.csv"), rd("killswitch.csv")
if not er.empty: er = er[(er.ts >= W0) & (er.ts <= W1 + 3600)]
if not ks.empty: ks = ks[(ks.ts >= W0) & (ks.ts <= W1 + 3600)]
# spread
sn = rd("snapshots.csv"); spr = {}   # snapshot: SEMUA (sebelum + selama forward) untuk estimasi spread
if not sn.empty:
    sn["sp"] = (sn.ask - sn.bid) / ((sn.ask + sn.bid) / 2) * 100
    spr = {"median_all": sn.sp.median(), "assumed_bt": cfg.get("backtest_spread_pct"), "n": len(sn),
           "per_pair": sn.groupby("pair").sp.median().to_dict()}
# order table + deviasi fill vs harga sinyal
ot = []
if not orders.empty:
    o = orders.copy(); o["dev_pct"] = (o.fill - o.signal_price) / o.signal_price * 100
    ot = o.sort_values("ts").to_dict("records")

out = cl({"cfg": cfg, "generated": pd.Timestamp.now(tz="Asia/Jakarta").strftime("%Y-%m-%d %H:%M WIB"),
    "bt": {"eq": eq_m(bt_eq, True), "tr": tr_m(bt_tr), "bh": bh(bt_a, bt_b)},
    "btw": {"eq": eq_m(btw_eq), "tr": tr_m(btw_tr)},
    "fw": {"eq": eq_m(fw_eq), "tr": tr_m(fw_tr), "bh": bh(fa, fb)},
    "sig": sig, "fills": {"rows": fills, "n_fw": len(fw_tr), "n_bt": len(btw_tr)}, "up": up, "n_err": len(er), "errors": er.tail(200).to_dict("records"), "kill": ks.to_dict("records"),
    "spr": spr, "orders": ot,
    "series": {k: v[["date", "equity"]].values.tolist() for k, v in [("bt", bt_eq), ("btw", btw_eq), ("fw", fw_eq)] if not v.empty},
    "btc": btc[["date", "close"]].values.tolist() if not btc.empty else []})
json.dump(out, open(R / "angka.json", "w"), ensure_ascii=False, indent=1)
t = (R / "dashboard_template.html").read_text(encoding="utf-8")
open(R / "dashboard.html", "w", encoding="utf-8").write(t.replace("/*__DATA__*/null", json.dumps(out, ensure_ascii=False).replace("</", "<\\/")))
print("OK: dashboard.html + angka.json dibuat dari", D)
