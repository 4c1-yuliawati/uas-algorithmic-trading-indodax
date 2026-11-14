# Refleksi: backtest vs forward test (LAPORAN SEMENTARA)

> **Status:** dikumpulkan 14 Nov 2026 23:xx WIB sebagai laporan sementara. Forward test berjalan 12 Nov 23:00 WIB s/d 22 Nov 2026 23:00 WIB dan **belum selesai** (baru 4 candle 12 jam yang tutup). Angka forward di bawah belum cukup untuk kesimpulan; bagian yang belum bisa dihitung ditandai *belum tersedia*. Versi lengkap akan dikirim setelah 22 Nov bila diizinkan.
*Draf dihasilkan otomatis dari `angka.json` (2026-11-14 23:06 WIB). Semua angka dapat dihitung ulang dengan `python hitung_ulang.py`.*

## 1. Hasil
- Backtest penuh (4.0 th): return +81.66%, CAGR +16.08%, MDD -32.29%, 69 trade, buy&hold BTC/IDR +409.42%.
- Jendela forward, backtest: return n/a, MDD n/a, 0 trade.
- Forward test: return +0.00%, MDD +0.00%, 0 trade; buy&hold BTC/IDR -7.19%.
- Pembanding: buy&hold BTC/IDR pada periode backtest +409.42% vs strategi +81.66% — strategi tidak mengalahkan buy&hold; return trend-following biasanya menukar sebagian kenaikan dengan proteksi drawdown (MDD strategi -32.29%).
- **Gap forward − backtest: n/a poin persentase** pada jendela yang sama.

## 2. Kecocokan sinyal
**Belum tersedia (laporan sementara).** Pembanding sinyal backtest pada jendela forward memerlukan data historis Indodax yang diperbarui sampai 14 Nov (`update_hist.py` + `backtest.py --window`), yang belum dijalankan. Yang sudah pasti: 5 candle diproses bot, 40 sinyal tercatat, seluruhnya HOLD, tanpa error.

## 3. Sumber selisih (dalam angka)
- Trade forward 0 vs backtest 0: tidak ada pasangan trade untuk dibandingkan fill-nya. Dengan 0 trade, kecocokan dinilai dari log sinyal.
- Spread: median semua snapshot (376 snapshot) = 0.136% vs asumsi backtest 0.130% (selisih 0.006 pp). adaidr: 0.188%; bnbidr: 0.655%; btcidr: 0.020%; dogeidr: 0.167%; ethidr: 0.059%; solidr: 0.116%; trxidr: 0.420%; xrpidr: 0.080%

## 4. Stabilitas bot
- Uptime: 4 dari 4 candle = 100.0%; 39 panggilan tercatat; keterlambatan median 40.6 mnt, maks 59.2 mnt setelah candle tutup.
- Error tercatat: 0; pemakaian kill switch: 0.
- Dampak penjadwal luar (GitHub Actions sering terlambat 5–30 menit): sinyal tetap dari candle tertutup sehingga tidak berubah, tetapi harga fill bergeser sebesar pergerakan harga selama keterlambatan.

## 5. Keterbatasan
- Bias survivorship: universe dipilih dari pair Indodax yang masih ada sekarang (kriteria likuiditas diukur Juli–September 2022, tetapi data pair yang delisting tidak tersedia).
- 10 hari (~20 candle 12 jam) terlalu pendek untuk kesimpulan statistik; selisih return lebih mencerminkan noise dan biaya daripada edge strategi.
- Fee: lihat `config.json` (`fee_status`) dan sumber yang dicantumkan di dashboard.
- Strategi trend-following kalah dari buy&hold BTC pada bull market panjang; return bukan kriteria nilai.

## 6. Perbaikan bug selama forward test
Aturan strategi (`strategy.py`, parameter di `config.json`, universe) tidak diubah sejak freeze (commit `2210fbc`, 12 Nov 2026 22:12 WIB). Perubahan infrastruktur/alat setelah freeze (rinci di `PERUBAHAN_PASCA_FREEZE.md`):
1. `.github/workflows/tick.yml`: pemicu jadwal menjadi menit 7 dan 37 tiap jam (commit `2437af9`), karena run terjadwal GitHub sering tertunda.
2. `export_logs.py`: ditambah mode offline (`LOG_FILE`) untuk membaca `log_mentah.json`.
3. `hitung_ulang.py`: jumlah candle yang diharapkan pada metrik uptime dibatasi sampai log terakhir (laporan sementara), agar uptime tidak dibagi dengan seluruh 10 hari.

## 7. Catatan temuan sementara
- **Keterlambatan penjadwal nyata:** keempat candle forward diproses 12,7 s/d 59 menit setelah candle tutup (median 40,6 menit), karena GitHub Actions menunda run terjadwal. Pemicu menit ke-37 (ditambah setelah freeze) belum terbukti mengurangi keterlambatan. Pada candle yang ada sinyalnya, jeda ini langsung menjadi selisih harga isian vs backtest.
- **Spread:** median terukur dari 376 snapshot forward 0,136% vs asumsi backtest 0,13%, cukup cocok untuk BTC, ETH, XRP, SOL, tetapi jauh lebih lebar untuk BNB (0,66%) dan TRX (0,42%). Backtest memakai satu angka spread untuk semua pair sehingga biaya BNB/TRX di backtest kemungkinan terlalu rendah.
- **Slippage:** belum ada order forward, jadi asumsi 0,05% belum bisa diverifikasi.
- **Tanpa trade:** dalam 4 candle pertama semua sinyal HOLD sehingga tidak ada order. Backtest menghasilkan 69 trade dalam 4 tahun (sekitar 1-2 per 10 hari), jadi 0 trade pada jendela pendek masih wajar.
