# Refleksi: backtest vs forward test (FINAL, 10 hari)

> Forward test: 12 Nov 2026 23:00 WIB s/d 22 Nov 2026 23:00 WIB (20 candle 12 jam, 8 pair). Freeze: commit `2210fbc`, 12 Nov 2026 22:12 WIB. Menggantikan laporan sementara 14 Nov.
*Angka dihasilkan otomatis dari `angka.json` (2026-11-23 21:15 WIB). Semua angka dapat dihitung ulang dengan `python hitung_ulang.py`.*

## 1. Hasil
- Backtest penuh (4.0 th): return +81.66%, CAGR +16.08%, MDD -32.29%, 69 trade, buy&hold BTC/IDR +409.42%.
- Jendela forward, backtest: return +0.00%, MDD +0.00%, 0 trade.
- Forward test: return +0.00%, MDD +0.00%, 0 trade; buy&hold BTC/IDR -15.83%.
- Pembanding: buy&hold BTC/IDR pada periode backtest +409.42% vs strategi +81.66% — strategi tidak mengalahkan buy&hold; return trend-following biasanya menukar sebagian kenaikan dengan proteksi drawdown (MDD strategi -32.29%).
- **Gap forward − backtest: 0.00 poin persentase** pada jendela yang sama.

## 2. Kecocokan sinyal
160 pasangan candle×pair (20 candle × 8 pair) dibandingkan; kecocokan 100.00%, selisih 0. Semua 160 sinyal pada kedua sisi adalah HOLD: tidak ada persilangan EMA20/EMA50 yang memenuhi syarat beli (EMA200 + ADX>20) maupun jual selama 10 hari. Kecocokan ini membuktikan bahwa kode sinyal bot dan backtest identik pada data yang sama, tetapi karena tidak ada sinyal BUY/SELL, **ia tidak menguji eksekusi order**. Hal itu hanya diuji di simulasi offline (`tests/sim_bot.py`: 1.448 sinyal, 0 beda, 2 order).

## 3. Sumber selisih (dalam angka)
- Trade forward 0 vs backtest 0: tidak ada pasangan trade untuk dibandingkan fill-nya. Dengan 0 trade, kecocokan dinilai dari log sinyal.
- Slippage dan fill: **tidak dapat dibandingkan**, karena 0 order forward. Asumsi slippage 0,05% tetap belum terverifikasi oleh data live.
- Spread: median semua snapshot (1952 snapshot) = 0.141% vs asumsi backtest 0.130% (selisih 0.011 pp). adaidr: 0.216%; bnbidr: 0.674%; btcidr: 0.029%; dogeidr: 0.183%; ethidr: 0.076%; solidr: 0.106%; trxidr: 0.387%; xrpidr: 0.090%. Median agregat cocok dengan asumsi, tetapi spread nyata sangat berbeda antar pair: BNB (0,67%) dan TRX (0,39%) 3–5 kali lebih lebar dari asumsi 0,13%, sedangkan BTC hanya 0,03%. Asumsi satu angka untuk semua pair terlalu rendah untuk BNB/TRX dan terlalu tinggi untuk BTC/ETH/SOL.

## 4. Stabilitas bot
- Uptime: 20 dari 20 candle = 100.0%; 225 panggilan tercatat; keterlambatan median 19.4 mnt, maks 95.6 mnt setelah candle tutup.
- Error tercatat: 0; pemakaian kill switch: 0.
- Rincian keterlambatan: dari 20 candle di jendela forward, median 19,4 menit setelah candle tutup, sebagian besar 5–25 menit, dan 6 candle terlambat 53–96 menit. Keterlambatan ini berasal dari GitHub Actions (jadwal terkadang bergeser 1 jam lebih), bukan dari bot atau Vercel. Pemicu tambahan menit ke-37 (ditambahkan setelah freeze) tidak menghilangkan pola ini.
- Dampak penjadwal luar (GitHub Actions sering terlambat 5–30 menit): sinyal tetap dari candle tertutup sehingga tidak berubah, tetapi harga fill bergeser sebesar pergerakan harga selama keterlambatan.

## 5. Keterbatasan
- Bias survivorship: universe dipilih dari pair Indodax yang masih ada sekarang (kriteria likuiditas diukur Juli–September 2022, tetapi data pair yang delisting tidak tersedia).
- 10 hari (~20 candle 12 jam) terlalu pendek untuk kesimpulan statistik; selisih return lebih mencerminkan noise dan biaya daripada edge strategi.
- Fee: lihat `config.json` (`fee_status`) dan sumber yang dicantumkan di dashboard.
- Strategi trend-following kalah dari buy&hold BTC pada bull market panjang; return bukan kriteria nilai.

## 6. Perbaikan bug selama forward test
Aturan strategi (`strategy.py`, parameter di `config.json`, universe) tidak diubah sejak freeze `2210fbc` (audit.py memverifikasi). Tidak ada perbaikan bug pada bot (`api/`) setelah freeze. Perubahan di luar aturan (rinci di `PERUBAHAN_PASCA_FREEZE.md`):
1. `.github/workflows/tick.yml`: jadwal `7 * * * *` -> `7,37 * * * *` (commit `2437af9`, 12 Nov 2026), mitigasi keterlambatan jadwal. Tidak terbukti mengurangi keterlambatan.
2. `export_logs.py`: mode offline `LOG_FILE` (14 Nov), `hitung_ulang.py`: batas `expected` pada uptime (14 Nov). Keduanya hanya alat laporan.
Sebelum freeze (tercatat di riwayat git): perbaikan konektivitas Indodax (User-Agent browser karena Cloudflare memblokir UA bot; `server_time` dalam milidetik; bucket 12 jam yang belum tutup dibuang). Semuanya selesai dan diuji sebelum 12 Nov 22:12 WIB.

## 7. Kesimpulan
- Bot berjalan stabil selama 10 hari penuh: 20 dari 20 candle diproses, 0 error, kill switch tidak pernah dipakai, state dan log konsisten. Idempotency bekerja (221 panggilan duplikat dilewati dengan benar).
- Sinyal bot cocok 100% dengan backtest pada jendela yang sama. Hasil keduanya identik: 0 trade, return 0,00%, sementara buy&hold BTC/IDR -15,83% pada periode yang sama.
- Karena tidak ada order, **realisme eksekusi (fill di bid/ask live, slippage, biaya) tidak teruji pada data live**. Kesimpulan tentang hal itu bergantung pada simulasi offline dan pengukuran spread, bukan trade nyata.
- Temuan yang bernilai: (1) keterlambatan penjadwal eksternal hingga 96 menit, yang pada candle bersinyal akan menggeser harga isian; (2) spread tidak seragam antar pair, sehingga asumsi biaya satu angka di backtest kurang akurat untuk BNB dan TRX.
- Jika diulang: pakai penjadwal yang lebih tepat waktu, spread per pair di backtest, dan jendela forward lebih panjang atau lebih banyak pair agar peluang sinyal muncul lebih besar.
