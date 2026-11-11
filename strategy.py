"""Strategi Trend Following (port dari Trend_Following.afl). DIPAKAI SAMA oleh backtest.py dan api/tick.py.
Beli : EMA(20) cross-up EMA(50) DAN close > EMA(200) DAN ADX(14) > 20  (hanya bila flat)
Jual : EMA(50) cross-up EMA(20) (hanya bila punya posisi). Tanpa stop-loss (sama seperti AFL)."""
P = dict(fast=20, slow=50, trend=200, adx=14, min_adx=20)

def ema(x, n):
    a, o = 2.0 / (n + 1), []
    for i, v in enumerate(x):
        o.append(v if i == 0 else a * v + (1 - a) * o[-1])
    return o

def adx(h, l, c, n):
    """ADX Wilder"""
    N = len(c); out = [None] * N
    if N < 2 * n + 1: return out
    tr, pdm, mdm = [0.0] * N, [0.0] * N, [0.0] * N
    for i in range(1, N):
        up, dn = h[i] - h[i - 1], l[i - 1] - l[i]
        pdm[i] = up if up > dn and up > 0 else 0.0
        mdm[i] = dn if dn > up and dn > 0 else 0.0
        tr[i] = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
    s_tr, s_p, s_m = sum(tr[1:n + 1]), sum(pdm[1:n + 1]), sum(mdm[1:n + 1])
    dx = {}
    for i in range(n, N):
        if i > n:
            s_tr = s_tr - s_tr / n + tr[i]; s_p = s_p - s_p / n + pdm[i]; s_m = s_m - s_m / n + mdm[i]
        pdi = 100 * s_p / s_tr if s_tr else 0; mdi = 100 * s_m / s_tr if s_tr else 0
        dx[i] = 100 * abs(pdi - mdi) / (pdi + mdi) if pdi + mdi else 0
    a = sum(dx[i] for i in range(n, 2 * n)) / n; out[2 * n - 1] = a
    for i in range(2 * n, N):
        a = (a * (n - 1) + dx[i]) / n; out[i] = a
    return out

def raw_signals(bars, p=P):
    """bars: list dict(o,h,l,c,v) urut waktu, SEMUA sudah tertutup. Return (buy[], sell[]) mentah per bar."""
    c = [b["c"] for b in bars]; h = [b["h"] for b in bars]; l = [b["l"] for b in bars]
    f, s, t, a = ema(c, p["fast"]), ema(c, p["slow"]), ema(c, p["trend"]), adx(h, l, c, p["adx"])
    buy, sell = [False] * len(c), [False] * len(c)
    for i in range(1, len(c)):
        buy[i] = f[i] > s[i] and f[i - 1] <= s[i - 1] and c[i] > t[i] and a[i] is not None and a[i] > p["min_adx"]
        sell[i] = s[i] > f[i] and s[i - 1] <= f[i - 1]
    return buy, sell

def decide(raw_buy, raw_sell, in_pos):
    """ExRem: BUY hanya bila flat, SELL hanya bila punya posisi."""
    if in_pos and raw_sell: return "SELL"
    if not in_pos and raw_buy: return "BUY"
    return "HOLD"
