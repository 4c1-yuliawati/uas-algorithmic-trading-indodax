import json, time, datetime as dt
from http.server import BaseHTTPRequestHandler
from _core import *
from strategy import raw_signals, decide
TF = CFG["tf_sec"]; WIB = dt.timezone(dt.timedelta(hours=7)); U = CFG["universe"]
FB, FS = CFG["fee_buy_pct"] / 100, CFG["fee_sell_pct"] / 100
def jl(k): v = redis("GET", k); return json.loads(v) if v else None
def window_ok(w, tf): return all(x[2] and (i == 0 or x[0] - w[i - 1][0] == tf) for i, x in enumerate(w))
def err(typ, msg, **k): log("errors", dict(ts=int(time.time()), type=typ, msg=str(msg)[:300], **k))

def run():
    t_call = int(time.time()); out = {"ts": t_call}
    try: now = server_time()
    except Exception as e: err("SERVER_TIME", e); now = t_call
    cand = now // TF * TF - TF                               # candle 12 jam tertutup terakhir
    st = jl("state") or dict(cash=CFG["capital"], pos={}, last={}, day=None, handled={})
    kill = os.environ.get("KILL_SWITCH") == "1" or redis("GET", "kill") == "1"
    if kill: log("kill", dict(ts=t_call, action="KILL_SWITCH_ACTIVE_TICK_DILEWATI_TRADING"))
    books, snap = {}, []
    for p in U:                                              # order book live (+ snapshot tiap panggilan)
        try:
            b, a = depth(p); books[p] = (b, a)
            if b and a: snap.append(dict(ts=t_call, pair=p, bid=b[0][0], ask=a[0][0]))
        except Exception as e: err("DEPTH", e, pair=p)
    for s in snap: log("snaps", s)
    def bid(p): return books[p][0][0][0] if p in books and books[p][0] else st["last"].get(p)
    eq = st["cash"] + sum(q["qty"] * (bid(p) or q["fill"]) for p, q in st["pos"].items())
    for p in st["pos"]:
        if p in books and books[p][0]: st["last"][p] = books[p][0][0][0]
    dk = (dt.datetime.fromtimestamp(now, dt.timezone.utc) + dt.timedelta(hours=7)).strftime("%Y-%m-%d")
    if not st["day"] or st["day"]["key"] != dk:             # panggilan pertama setelah 00.00 WIB
        st["day"] = dict(key=dk, start=eq, blocked=False); log("equity", dict(ts=t_call, date=dk, equity=eq))
    blocked = (eq / st["day"]["start"] - 1) * 100 <= -CFG["daily_loss_limit_pct"]
    if blocked and not st["day"]["blocked"]:
        st["day"]["blocked"] = True; err("DAILY_LOSS_LIMIT", f"equity {eq:.0f} vs awal hari {st['day']['start']:.0f}; buy dihentikan sampai 00.00 WIB")
    rec = dict(ts=t_call, candle_ts=cand, processed_ts=None, status="SKIP", server_now=now, equity=eq)
    # --- idempotency: satu candle diproses sekali (lock atomik SET NX) ---
    if kill: rec["status"] = "KILL_SWITCH"
    elif redis("GET", f"done:{cand}"): rec["status"] = "DUPLIKAT_DILEWATI"
    elif redis("SET", f"lock:{cand}", str(t_call), "NX", "EX", 900) is None: rec["status"] = "LOCKED"
    else:
        try:
            process(st, cand, now, books, eq, blocked, t_call)
            redis("SET", f"done:{cand}", str(t_call)); rec.update(processed_ts=int(time.time()), status="PROCESSED")
        except Exception as e:
            err("PROCESS", e, candle_ts=cand); redis("DEL", f"lock:{cand}"); rec["status"] = "ERROR"   # panggilan berikutnya mencoba lagi
    redis("SET", "state", json.dumps(st)); log("calls", rec); return {**out, **rec}

def process(st, cand, now, books, eq, blocked, t_call):
    done = st["handled"].setdefault(str(cand), [])
    for p in U:
        if p in done: continue
        c4 = candles_4h(p, now); bars = bars_12h(c4, TF); time.sleep(0.3)
        why = None
        if not bars or bars[-1][0] != cand or not bars[-1][2]: why = "candle tertutup terakhir tidak ada/lebih tua dari 2xTF"
        elif len(bars) < 260: why = "riwayat < 260 bar"
        elif not window_ok(bars[-260:], TF): why = "candle hilang di jendela indikator"
        elif bars[-1][1]["c"] <= 0 or bars[-1][1]["v"] <= 0: why = "harga/volume nol"
        b, a = books.get(p, ([], []))
        if not why and (not b or not a): why = "order book kosong"
        if not why and (a[0][0] - b[0][0]) / ((a[0][0] + b[0][0]) / 2) > 0.02: why = "spread bid-ask > 2%"
        full = [x[1] for x in bars if x[2]]
        # hanya bar lengkap; riwayat tua yang bolong tidak mengubah sinyal bar terakhir (EMA meluruh)
        bs, ss = raw_signals(full) if full else ([False], [False]); sig = c = None
        c = full[-1]["c"] if full else None
        act = decide(bs[-1], ss[-1], p in st["pos"]) if not why else "INVALID"
        log("signals", dict(candle_ts=cand, pair=p, signal=act, o=full[-1]["o"] if full else None, h=full[-1]["h"] if full else None, l=full[-1]["l"] if full else None, c=c, v=full[-1]["v"] if full else None))
        if why: err("DATA_INVALID", why, pair=p, candle_ts=cand)
        elif act == "SELL" or (p in st["pos"] and st["pos"][p].get("exit_pending")): sell(st, p, b, a, c, cand)
        elif act == "BUY":
            if blocked: err("BUY_DITOLAK", "daily loss limit aktif", pair=p)
            elif len(st["pos"]) >= CFG["max_positions"]: err("BUY_DITOLAK", "batas posisi terbuka", pair=p)
            else: buy(st, p, b, a, c, cand, eq)
        done.append(p); redis("SET", "state", json.dumps(st))   # simpan per pair -> aman bila terpotong
    for p in [p for p, q in st["pos"].items() if q.get("exit_pending") and p not in done]: sell(st, p, *books.get(p, ([], [])), None, cand)

def order(p, side, qty, b, a, fill, fee, sp, cand):
    log("orders", dict(ts=int(time.time()), pair=p, side=side, qty=qty, best_bid=b[0][0], best_ask=a[0][0], fill=fill, fee=fee, signal_price=sp, candle_ts=cand))
def buy(st, p, b, a, sp, cand, eq):
    size = min(CFG["alloc_pct"] / 100 * eq, st["cash"]) / (1 + FB)
    if size < CFG["min_order"]: return err("BUY_DITOLAK", f"nilai order {size:.0f} < minimum {CFG['min_order']}", pair=p)
    qty = int(size / a[0][0] * 1e8) / 1e8
    for _ in range(20):                                       # kurangi qty sampai (biaya+fee) muat di kas
        avg, f = walk(a, qty)
        if f < qty - 1e-12: return err("BUY_DITOLAK", "kedalaman order book tidak cukup", pair=p)
        if avg * qty * (1 + FB) <= st["cash"]: break
        qty = int(qty * 0.995 * 1e8) / 1e8
    cost = avg * qty
    if cost < CFG["min_order"]: return err("BUY_DITOLAK", "di bawah minimum order", pair=p)
    fee = cost * FB; st["cash"] -= cost + fee; st["pos"][p] = dict(qty=qty, fill=avg, fee=fee, ts=int(time.time()))
    order(p, "BUY", qty, b, a, avg, fee, sp, cand)
def sell(st, p, b, a, sp, cand):
    q = st["pos"][p]
    if not b or not a: q["exit_pending"] = True; return err("SELL_TERTUNDA", "order book kosong", pair=p)
    avg, f = walk(b, q["qty"])
    if f <= 0: q["exit_pending"] = True; return err("SELL_TERTUNDA", "tidak ada bid", pair=p)
    gross = avg * f; fee = gross * FS; st["cash"] += gross - fee
    order(p, "SELL", f, b, a, avg, fee, sp if sp is not None else q["fill"], cand)
    if f >= q["qty"] - 1e-12: del st["pos"][p]
    else: q["qty"] -= f; q["exit_pending"] = True

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not authorized(self.headers): self.send_response(401); self.end_headers(); return
        try: res, code = run(), 200
        except Exception as e:
            res, code = {"error": str(e)}, 500
            try: err("TICK_FATAL", e)
            except Exception: pass
        self.send_response(code); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(json.dumps(res).encode())
