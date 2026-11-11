# Strategi tertulis & catatan perubahan dari UTS
**Sumber:** `Trend_Following.afl` (UTS, saham). Long-only, tanpa short/margin/leverage. Timeframe **12 jam** (bar 00:00 & 12:00 UTC = 07.00 & 19.00 WIB), disusun dari bar 4 jam Indodax.

| Aturan | Nilai |
|---|---|
| Masuk (hanya saat flat) | EMA(20) cross-up EMA(50) **dan** Close > EMA(200) **dan** ADX(14, Wilder) > 20 |
| Keluar (hanya saat punya posisi) | EMA(50) cross-up EMA(20). Tanpa stop-loss (sama dgn UTS) |
| Sinyal | hanya dari candle **tertutup**; fungsi sinyal sama persis di `strategy.py` untuk backtest dan bot |
| Eksekusi backtest | sinyal di close bar *t* → fill di open bar *t+1* ± (spread/2 + slippage) + fee taker (setara `SetTradeDelays(1,1,1,1)`, harga Open di AFL) |
| Eksekusi bot | segera setelah candle tertutup: beli di ask / jual di bid dari order book live (habiskan level berikutnya, harga rata-rata); bukan mid/close |
| Sizing | 20% equity per posisi, maks 5 posisi terbuka, order ≥ Rp25.000, kuantitas dibulatkan ke bawah (8 desimal) |
| Daily loss limit | equity turun ≥ 3% dari awal hari WIB (00.00 WIB) → tidak buka posisi baru sampai hari berikutnya |
| Kill switch | env `KILL_SWITCH=1` atau `/api/kill?on=1` (flag Redis); semua pemakaian dicatat |
| Parameter | 20 / 50 / 200 / 14 / 20 — sama dgn AFL, **tidak dioptimasi** |

## Perubahan dari versi UTS
1. Timeframe harian-saham → 12 jam agar ada ±20 candle selama 10 hari forward.
2. Ditambah sizing, daily loss limit, kill switch, validasi data, idempotency (wajib oleh soal). **Aturan masuk/keluar tidak diubah.**
3. Fill: open+delay 1 bar (AFL) → bid/ask live + fee taker. ADX diimplementasi manual (Wilder), dapat berbeda tipis dari AmiBroker.

## Universe (8 pair IDR) dan anti-survivorship
Kandidat: 209 pair di `indodax_12h` (data onaldhi). Dikeluarkan: stablecoin (USDT, USDC) dan `JKSE.csv` (duplikat BTC). Peringkat likuiditas = median nilai harian (close × volume) **1 Jul–30 Sep 2022**, yaitu 3 bulan sebelum backtest dimulai (1 Okt 2022), bukan likuiditas hari ini. Syarat tambahan: riwayat ≥ 200 bar sebelum awal backtest dan masih likuid saat freeze (median harian Q3-2026 ≥ Rp100 juta). Terpilih: BTC, ETH, DOGE, ADA, XRP, BNB, SOL, TRX. Pair yang likuid di 2022 tetapi kini tidak (DEP, ZIL, VRA, SAND, ETC, dll.) keluar.
**Keterbatasan (wajib di refleksi):** dataset hanya memuat pair yang masih terdaftar; pair yang sudah delisting tidak ada, sehingga bias survivorship berkurang tetapi tidak hilang.

## Biaya (isi dari sumber resmi sebelum freeze)
Lihat `config.json`: `fee_buy_pct`, `fee_sell_pct`, `fee_sources` (URL + tanggal akses), `min_order` (Rp25.000 bila lebih ketat dari `/api/pairs`).
